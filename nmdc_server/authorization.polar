actor User {}

resource SubmissionMetadata {
    roles = ["editor", "owner", "viewer", "metadata_contributor", "reviewer];
    permissions = [
        "read",
        "edit_contributors",
        "edit_metadata",
        "edit_context",
        "read_comments",
        "write_comments"
    ];

    "read" if "viewer";
    "edit_metadata" if "metadata_contributor";
    "read_comments" if "metadata_contributor";
    "edit_context" if "editor";
    "edit_contributors" if "owner";
    "write_comments" if "reviewer";

    "viewer" if "metadata_contributor";
    "metadata_contributor" if "editor";
    "editor" if "owner";
}

has_role(user: User, name: String, submission: SubmissionMetadata) if
    role in submission.roles and
    role matches { role: name, user_orcid: user.orcid}
