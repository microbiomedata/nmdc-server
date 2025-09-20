<!-- 
    Note: The `description` kwarg of the `FastAPI` constructor supports CommonMark syntax,
          according to the constructor's docstring.
-->

**About this API:**
This API provides NMDC applications access to publicly-available NMDC data
as well as the logged-in user's own submissions.
It was designed to be accessed exclusively by
the [NMDC Data Portal]({{ nmdc_data_portal_url }}) and
the [NMDC Submission Portal]({{ nmdc_submission_portal_url }}).

**Want to access NMDC data from your own scripts and programs?**
Check out the [NMDC Runtime API]({{ runtime_api_url }}), which was
designed to be accessed by third-party scripts, programs, and other HTTP clients.

**NMDC developers:** To use authenticated endpoints of this API,
you must first obtain an Access Token by following the instructions in the
Developer Tools section [here]({{ developer_tools_url }}).
Once you have an Access Token, click the "Authorize" button on this page.
In the popup, paste the token in the "Value" field and click "Authorize".
