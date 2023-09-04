from pymongo import MongoClient
import time
from typing import List, Dict
import envo

start = time.time()

client = MongoClient()

envo.mongo_load(client)

omics_types = [
    "Metagenome",
    "Organic Matter Characterization",
    "Metatranscriptome",
    "Proteomics",
    "Metabolomics",
]

study_transformed_aggregation: List[Dict] = [
    {
        "$lookup": {
            "from": "biosample_transformed",
            "localField": "id",
            "foreignField": "part_of",
            "as": "biosample",
        },
    },
    {
        "$lookup": {
            "from": "omics_processing_set",
            "localField": "biosample.id",
            "foreignField": "has_input",
            "as": "omics_processing",
        },
    },
    # Count the number of each omics_type and get it in the form [{"type": "Metagenome", "count": 100}, ...].
    # This one is a kind of beast in mongo aggregation programming.
    #
    # The pipeline in procedural code is roughly:
    #
    # omics_type_count_map = reduce_to_count_of_each_omics_type(omics_processing_array) (e.g. {"Metagenome": 100, "Metabolomics": 50, ...})
    # key_value_array = object_to_key_value_array(omics_type_count_map) (e.g. [{"k": "Metagenome", "v": 100}, {"k": "Metabolomics", "v": 50}, ...])
    # type_count_array = rename_key_value_to_type_count(key_value_array) (e.g. [{"type": "Metagenome", "count": 100}, {"type": "Metabolomics", "count": 50}, ...])
    # omics_processing_counts = sort_by_omics_type_name(type_count_array) (e.g. [{"type": "Metabolomics", "count": 50}, {"type": "Metagenome", "count": 100}, ...])
    {
        "$set": {
            "omics_processing_counts": {
                "$sortArray": {
                    "input": {
                        "$map": {
                            "input": {
                                "$objectToArray": {
                                    "$reduce": {
                                        "input": "$omics_processing",
                                        "initialValue": { omics_type: 0 for omics_type in omics_types },
                                        "in": {
                                            omics_type: {
                                                "$cond": {
                                                    "if": {"$eq": ["$$this.omics_type.has_raw_value", omics_type] },
                                                    "then": {"$add": [f"$$value.{omics_type}", 1]},
                                                    "else": f"$$value.{omics_type}",
                                                },
                                            }
                                            for omics_type in omics_types
                                        },
                                    },
                                },
                            },
                            "in": {
                                "type": "$$this.k",
                                "count": "$$this.v",
                            },
                        },
                    },
                    "sortBy": {"type": 1},
                },
            },
        },
    },
    {
        "$unset": "omics_processing",
    },
    # Count the number of biosamples
    {
        "$set": {
            "sample_count": {
                "$size": "$biosample"
            }
        }
    },
    {
        "$unset": "biosample",
    },
    {
        "$out": "study_transformed",
    },
]
print("Generating study_transformed...")
q = client.nmdc.study_set.aggregate(study_transformed_aggregation)
print("...done")




# A couple transforms needed for optimal queries
biosample_transformed_aggregation: List[Dict] = [
    # To filter by dates we need actual dates in the database
    {
        "$set": {
            "collection_date.has_date_value": {
                "$dateFromString": {
                    "dateString": "$collection_date.has_raw_value",
                },
            },
        },
    },
    # Lookup related omics_processing temporarily to derive some summary properties
    {
        "$lookup": {
            "from": "omics_processing_set",
            "localField": "id",
            "foreignField": "has_input",
            "as": "omics_processing",
        },
    },
    # Create an array of all the omics_processing types associated with this sample
    {
        "$set": {
            "multiomics": {
                "$sortArray": {
                    "input": {
                        # This set difference removes duplicate omics types and removes lipidomics
                        "$setDifference": [
                            "$omics_processing.omics_type.has_raw_value",
                            ["Lipidomics"],
                        ],
                    },
                    "sortBy": 1,
                },
            },
        },
    },
    # Add a count so we can sort by the number of types of omics_processing each sample has
    {
        "$set": {
            "multiomics_count": {
                "$size": "$multiomics"
            }
        }
    },
    # We don't want to actually store the related omics_processing
    {
        "$unset": "omics_processing",
    },
    # Save the result
    {
        "$out": "biosample_transformed",
    },
]

print("Generating biosample_transformed...")
q = client.nmdc.biosample_set.aggregate(biosample_transformed_aggregation)
print("...done")

def denormalize_analysis_aggregation(base_type):
    aggregation = []

    activity_types = {
        "mags_activity": "nmdc:MAGsAnalysisActivity",
        "metabolomics_analysis_activity": "nmdc:MetabolomicsAnalysisActivity",
        "metagenome_annotation_activity": "nmdc:MetagenomeAnnotation",
        "metagenome_assembly": "nmdc:MetagenomeAssembly",
        "metaproteomics_analysis_activity": "nmdc:MetaProteomicAnalysis",
        "metatranscriptome_activity": "nmdc:metaT",
        "nom_analysis_activity": "nmdc:NomAnalysisActivity",
    }

    for activity_type in activity_types:
        # Pull in activities and data_objects associated with each omics_processing
        aggregation.extend([
            {
                "$lookup": {
                    "from": f"{activity_type}_set",
                    "localField": "id" if base_type == "omics_processing" else "omics_processing.id",
                    "foreignField": "was_informed_by",
                    "as": activity_type,
                },
            },
            # Move this to after all analyses are concatenated - can be one step to get all data_object records
            {
                "$lookup": {
                    "from": "data_object_set",
                    "localField": f"{activity_type}.has_output",
                    "foreignField": "id",
                    "as": f"{activity_type}_data_object",
                    "pipeline": [
                        {"$set": {"activity_type": activity_types[activity_type]}},
                    ],
                },
            },
        ])

    aggregation.extend([
        # Lookup metagenome annotations
        {
            "$lookup": {
                "from": "functional_annotation_agg",
                "localField": "metagenome_annotation_activity.id",
                "foreignField": "metagenome_annotation_id",
                "as": "metagenome_annotation",
                "pipeline": [
                    {
                        "$set": {
                            "id": "$gene_function_id",
                            "activity_id": "$metagenome_annotation_id",
                        },
                    },
                    {"$unset": ["_id", "metagenome_annotation_id", "gene_function_id"]},
                ],
            },
        },
        # Lookup metaproteomics annotations
        {
            "$lookup": {
                "from": "metap_gene_function_aggregation",
                "localField": "metaproteomics_analysis_activity.id",
                "foreignField": "metaproteomic_analysis_id",
                "as": "metaproteomics_annotation",
                "pipeline": [
                    {
                        "$set": {
                            "id": "$gene_function_id",
                            "activity_id": "$metaproteomic_analysis_id",
                        },
                    },
                    {"$unset": ["_id", "metaproteomic_analysis_id", "gene_function_id"]},
                ],
            },
        },
        # Combine annotations into a single annotation array
        {
            "$set": {
                "gene_function": {
                    "$concatArrays": ["$metagenome_annotation", "$metaproteomics_annotation"]
                }
            },
        },
        {
            "$unset": ["metagenome_annotation", "metaproteomics_annotation"],
        },
        # Combine all activities into a single activity array
        {
            "$set": {
                "activity": {
                    "$concatArrays": [f"${activity_type}" for activity_type in activity_types]
                }
            }
        },
        # Remove the monstrous has_peptide_quantifications array to speed search
        {
            "$set": {
                "activity": {
                    "$map": {
                        "input": "$activity",
                        "as": "d",
                        "in": {
                            "$setField": {
                                "field": "has_peptide_quantifications",
                                "value": "$$REMOVE",
                                "input": "$$d"
                            }
                        }
                    }
                },
            }
        },
        # We are done with the separate activity types since they are all in the activity array now
        {
            "$unset": list(activity_types.keys()),
        },
    ])

    aggregation.extend([
        # Combine all data objects into a single data_object array
        {
            "$set": {
                "data_object": {
                    "$concatArrays": [f"${activity_type}_data_object" for activity_type in activity_types]
                }
            }
        },
        # We no longer need the individual data_object fields
        {
            "$unset": [f"{activity_type}_data_object" for activity_type in activity_types]
        },
    ])

    return aggregation


biosample_denormalized_aggregation: List[Dict] = [
    {
        "$lookup": {
            "from": "study_transformed",
            "localField": "part_of",
            "foreignField": "id",
            "as": "study",
        },
    },
    {
        "$lookup": {
            "from": "omics_processing_set",
            "localField": "id",
            "foreignField": "has_input",
            "as": "omics_processing",
        },
    },
]

biosample_denormalized_aggregation += denormalize_analysis_aggregation("biosample")

biosample_denormalized_aggregation += [
    {
        "$out": "biosample_denormalized",
    },
]

print("Generating biosample_denormalized...")
q = client.nmdc.biosample_transformed.aggregate(biosample_denormalized_aggregation)
print("...done")



omics_processing_denormalized_aggregation: List[Dict] = [
    {
        "$lookup": {
            "from": "biosample_transformed",
            "localField": "has_input",
            "foreignField": "id",
            "as": "biosample",
        },
    },
    {
        "$lookup": {
            "from": "study_transformed",
            "localField": "biosample.part_of",
            "foreignField": "id",
            "as": "study",
        },
    },
]

omics_processing_denormalized_aggregation += denormalize_analysis_aggregation("omics_processing")

omics_processing_denormalized_aggregation += [
    {
        "$out": "omics_processing_denormalized",
    },
]

print("Generating omics_processing_denormalized...")
q = client.nmdc.omics_processing_set.aggregate(omics_processing_denormalized_aggregation)
print("...done")

end = time.time()
print(f"Completed in {end - start}s")
