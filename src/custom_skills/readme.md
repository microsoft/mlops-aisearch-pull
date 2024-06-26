# Custom Skills

This folder contains custom skills to use with an Azure AI Search Indexer.

## Local Setup

- Open the devcontainer in VS Code and execute `pip install -r requirements.txt` to install dependencies.
- Copy `local.settings.json.template` to `local.settings.json` and populate the required environment variables
- Run the function app with `func host start --python`

## Functions

### Chunk

This function will accept accept a filename for a pdf to break into chunks.
The chunking strategy is currently hardcoded.
Review the local setup for the environment variables used in the project.

#### Testing Chunk

- Upload the pdf documents from the `data` folder to a storage account container
- Use postman to make a POST request to the function endpoint
- Upon completion of the request, you should get a 200 response from the function with a response containing the chunks contained in the `page_content` of each data list item.

Sample body for the request:

```json
{
    "values": [
        {
            "recordId": "r1",
            "data": {
                "filename": "PerksPlus.pdf"
            }
        }
    ]
}
```

Example Response:

```json
{
    "values": [
        {
            "recordId": "r1",
            "data": {
                "chunks": [
                    {
                        "page_content": "PerksPlus Health and Wellness  \nReimbursement Program for \nContoso Electronics Employees",
                        "metadata": {
                            "source": "/tmp/PerksPlus.pdf",
                            "page": 0
                        },
                        "type": "Document"
                    },
                    {
                        "page_content": "This document contains information generated using a language model (Azure OpenAI ). The information \ncontained in this document is only for demonstration purposes and does not reflect the opinions or \nbeliefs of Microsoft. Microsoft makes no representations or warranties of any kind, express or implied, \nabout the completeness, accuracy, reliability, suitability or availability with respect to the information \ncontained in this document.  \nAll rights reserved to Microsoft",
                        "metadata": {
                            "source": "/tmp/PerksPlus.pdf",
                            "page": 1
                        },
                        "type": "Document"
                    },
                ]
            },
            "errors": null,
            "warnings": null
        }
    ]
}
```

### VectorEmbed

This function accepts a list of chunks and creates vector embeddings for them.
Review the local setup for the environment variables used in the project.

#### Testing VectorEmbed

- Obtain the output from the Chunk function
- Use postman to make a POST request to the function endpoint
- Upon completion of the request, you should get a 200 response from the function with a response containing the vector embedding contained in the `contentVector` of each data list item.

Sample body for the request:

```json
{
    "values": [
        {
            "recordId": "r1",
            "data": {
                "chunk": {
                        "page_content": "PerksPlus Health and Wellness Reimbursement Program for Contoso Electronics Employees\n\nThis document contains information generated using a language model (Azure OpenAI). The information contained in this document is only for demonstration purposes and does not reflect the opinions or beliefs of Microsoft. Microsoft makes no representations or warranties of any kind, express or implied, about the completeness, accuracy, reliability, suitability or availability with respect to the information contained in this document.\n\nAll rights reserved to Microsoft",
                        "metadata": {
                            "source": "/tmp/tmp1_bu5os8/toydataset/PerksPlus.pdf",
                            "page": 1
                        },
                        "type": "Document"
                    }
            },
            "errors": null,
            "warnings": null
        }
    ]
}
```

Example Response:

```json
{
    "values": [
        {
            "recordId": "r1",
            "data": {
                "embedding": [
                    -0.004001418128609657,
                    0.003195576835423708,
                    ...
                    0.005602680146694183,
                    -0.01686708815395832
                ],
                "page": 1
            },
            "errors": null,
            "warnings": null
        }
    ]
}
```
