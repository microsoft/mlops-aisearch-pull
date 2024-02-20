# Custom Skills
This folder contains custom skills to use with Azure AI Search.

## Local Setup
- Open the devcontainer in VS Code and execute `pip install -r requirements.txt` to install dependencies.
- Copy `local.settings.json.template` to `local.settings.json` and populate the required environment variables
- Run the function app with `func host start --python`

## Functions

### ChunkVectorEmbed
This function will accept accept a filename for a pdf to chunk and insert into an Azure AI Search index.
It breaks the pdf into chunks, creates an embedding for each of those chunks, and then uploads the data to an index in Azure AI Search.
The chunking strategy is currently hardcode and the index name is configured with an environment variable.  Review the local setup for the environment variables used in the project.

#### Testing ChunkVectorEmbed
- Upload the pdf documents from the `data` folder to a storage account container
- Use postman to make a POST request to the function endpoint
- Upon completion of the request, you should get a 200 response from the function and there should be new entries in the AI Search index.

Sample body for the request:
```json
{
    "values": [
        {
            "recordId": "r1",
            "data": {
                "filename": "employee_handbook.pdf"
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
            "identifiers": [
                "bf3a94c7-3bcc-4681-bb8d-8e5ff79fcfa7",
                "50523525-aaee-4de9-8be1-30d91be6b78c"
            ],
            "data": [
                {
                    "id": "bf3a94c7-3bcc-4681-bb8d-8e5ff79fcfa7",
                    "filename": "employee_handbook.pdf",
                    "content": "Data Security Audits:\n\nContoso Electronics will conduct regular audits of our data security program to ensure that it is functioning as intended. Audits will cover topics such as system security, access control, and data protection.\n\nIf you have any questions or concerns about Contoso Electronics’ data security program, please contact our data security team. We are committed to keeping your data secure and we appreciate your continued trust. Thank you for being a valued customer.\n\nJob Roles\n\n1. Chief Executive Officer 2. Chief Operating Officer 3. Chief Financial Officer 4. Chief Technology Officer 5. Vice President of Sales 6. Vice President of Marketing 7. Vice President of Operations 8. Vice President of Human Resources 9. Vice President of Research and Development 10. Vice President of Product Management 11. Director of Sales 12. Director of Marketing 13. Director of Operations 14. Director of Human Resources",
                    "contentVector": [
                        0.004739957395941019,
                        -0.01657814346253872,
                        ...
                        -0.004576049279421568,
                        0.021542219445109367
                    ]
                },
                {
                    "id": "50523525-aaee-4de9-8be1-30d91be6b78c",
                    "filename": "employee_handbook.pdf",
                    "content": "15. Director of Research and Development 16. Director of Product Management 17. Senior Manager of Sales 18. Senior Manager of Marketing 19. Senior Manager of Operations 20. Senior Manager of Human Resources 21. Senior Manager of Research and Development 22. Senior Manager of Product Management 23. Manager of Sales 24. Manager of Marketing 25. Manager of Operations 26. Manager of Human Resources 27. Manager of Research and Development 28. Manager of Product Management 29. Sales Representative 30. Customer Service Representative",
                    "contentVector": [
                        -0.010118980892002583,
                        -0.014274303801357746,
                        ...
                        -0.03516634181141853,
                        0.013222647830843925
                    ]
                }
            ],
            "errors": null,
            "warnings": null
        }
    ]
}

```

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
                "filename": "employee_handbook.pdf"
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
            "filename": "employee_handbook.pdf",
            "data": [
                {
                    "page_content": "Data Security Audits:\n\nContoso Electronics will conduct regular audits of our data security program to ensure that it is functioning as intended. Audits will cover topics such as system security, access control, and data protection.\n\nIf you have any questions or concerns about Contoso Electronics’ data security program, please contact our data security team. We are committed to keeping your data secure and we appreciate your continued trust. Thank you for being a valued customer.\n\nJob Roles\n\n1. Chief Executive Officer 2. Chief Operating Officer 3. Chief Financial Officer 4. Chief Technology Officer 5. Vice President of Sales 6. Vice President of Marketing 7. Vice President of Operations 8. Vice President of Human Resources 9. Vice President of Research and Development 10. Vice President of Product Management 11. Director of Sales 12. Director of Marketing 13. Director of Operations 14. Director of Human Resources",
                    "metadata": {
                        "source": "/tmp/tmpq1lyk39c/data/employee_handbook.pdf"
                    }
                },
                {
                    "page_content": "15. Director of Research and Development 16. Director of Product Management 17. Senior Manager of Sales 18. Senior Manager of Marketing 19. Senior Manager of Operations 20. Senior Manager of Human Resources 21. Senior Manager of Research and Development 22. Senior Manager of Product Management 23. Manager of Sales 24. Manager of Marketing 25. Manager of Operations 26. Manager of Human Resources 27. Manager of Research and Development 28. Manager of Product Management 29. Sales Representative 30. Customer Service Representative",
                    "metadata": {
                        "source": "/tmp/tmpq1lyk39c/data/employee_handbook.pdf"
                    }
                }
            ],
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
            "filename": "employee_handbook.pdf",
            "data": [
                {
                    "page_content": "Data Security Audits:\n\nContoso Electronics will conduct regular audits of our data security program to ensure that it is functioning as intended. Audits will cover topics such as system security, access control, and data protection.\n\nIf you have any questions or concerns about Contoso Electronics’ data security program, please contact our data security team. We are committed to keeping your data secure and we appreciate your continued trust. Thank you for being a valued customer.\n\nJob Roles\n\n1. Chief Executive Officer 2. Chief Operating Officer 3. Chief Financial Officer 4. Chief Technology Officer 5. Vice President of Sales 6. Vice President of Marketing 7. Vice President of Operations 8. Vice President of Human Resources 9. Vice President of Research and Development 10. Vice President of Product Management 11. Director of Sales 12. Director of Marketing 13. Director of Operations 14. Director of Human Resources",
                },
                {
                    "page_content": "15. Director of Research and Development 16. Director of Product Management 17. Senior Manager of Sales 18. Senior Manager of Marketing 19. Senior Manager of Operations 20. Senior Manager of Human Resources 21. Senior Manager of Research and Development 22. Senior Manager of Product Management 23. Manager of Sales 24. Manager of Marketing 25. Manager of Operations 26. Manager of Human Resources 27. Manager of Research and Development 28. Manager of Product Management 29. Sales Representative 30. Customer Service Representative",
                }
            ]
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
            "identifiers": [
                "65630afa-0e70-43cc-b5a6-15a0ce2cb16e",
                "f4bb09c2-b60f-467b-94e1-878771f8bbf1"
            ],
            "data": [
                {
                    "id": "65630afa-0e70-43cc-b5a6-15a0ce2cb16e",
                    "filename": "employee_handbook.pdf",
                    "content": "Data Security Audits:\n\nContoso Electronics will conduct regular audits of our data security program to ensure that it is functioning as intended. Audits will cover topics such as system security, access control, and data protection.\n\nIf you have any questions or concerns about Contoso Electronics’ data security program, please contact our data security team. We are committed to keeping your data secure and we appreciate your continued trust. Thank you for being a valued customer.\n\nJob Roles\n\n1. Chief Executive Officer 2. Chief Operating Officer 3. Chief Financial Officer 4. Chief Technology Officer 5. Vice President of Sales 6. Vice President of Marketing 7. Vice President of Operations 8. Vice President of Human Resources 9. Vice President of Research and Development 10. Vice President of Product Management 11. Director of Sales 12. Director of Marketing 13. Director of Operations 14. Director of Human Resources",
                    "contentVector": [
                        0.004739957395941019,
                        -0.01657814346253872,
                        ...
                        -0.004576049279421568,
                        0.021542219445109367
                    ]
                },
                {
                    "id": "f4bb09c2-b60f-467b-94e1-878771f8bbf1",
                    "filename": "employee_handbook.pdf",
                    "content": "15. Director of Research and Development 16. Director of Product Management 17. Senior Manager of Sales 18. Senior Manager of Marketing 19. Senior Manager of Operations 20. Senior Manager of Human Resources 21. Senior Manager of Research and Development 22. Senior Manager of Product Management 23. Manager of Sales 24. Manager of Marketing 25. Manager of Operations 26. Manager of Human Resources 27. Manager of Research and Development 28. Manager of Product Management 29. Sales Representative 30. Customer Service Representative",
                    "contentVector": [
                        -0.010118980892002583,
                        -0.014274303801357746,
                        ...
                        -0.03516634181141853,
                        0.013222647830843925
                    ]
                }
            ],
            "errors": null,
            "warnings": null
        }
    ]
}
```

### IndexUpload
This function uses the output of `VectorEmbed` to upload data into an index specified in the environment variables.
Review the local setup for the environment variables used in the project.

#### Testing IndexUpload
- Obtain the output from the VectorEmbed function
- Use postman to make a POST request to the function endpoint
- Upon completion of the request, you should get a 200 response from the function with a response with a list of ids added to the index.

Sample body for the request:
```json
{
    "values": [
        {
            "recordId": "r1",
            "identifiers": [
                "65630afa-0e70-43cc-b5a6-15a0ce2cb16e",
                "f4bb09c2-b60f-467b-94e1-878771f8bbf1"
            ],
            "data": [
                {
                    "id": "65630afa-0e70-43cc-b5a6-15a0ce2cb16e",
                    "filename": "employee_handbook.pdf",
                    "content": "Data Security Audits:\n\nContoso Electronics will conduct regular audits of our data security program to ensure that it is functioning as intended. Audits will cover topics such as system security, access control, and data protection.\n\nIf you have any questions or concerns about Contoso Electronics’ data security program, please contact our data security team. We are committed to keeping your data secure and we appreciate your continued trust. Thank you for being a valued customer.\n\nJob Roles\n\n1. Chief Executive Officer 2. Chief Operating Officer 3. Chief Financial Officer 4. Chief Technology Officer 5. Vice President of Sales 6. Vice President of Marketing 7. Vice President of Operations 8. Vice President of Human Resources 9. Vice President of Research and Development 10. Vice President of Product Management 11. Director of Sales 12. Director of Marketing 13. Director of Operations 14. Director of Human Resources",
                    "contentVector": [
                        0.004739957395941019,
                        -0.01657814346253872,
                        ...
                        -0.004576049279421568,
                        0.021542219445109367
                    ]
                },
                {
                    "id": "f4bb09c2-b60f-467b-94e1-878771f8bbf1",
                    "filename": "employee_handbook.pdf",
                    "content": "15. Director of Research and Development 16. Director of Product Management 17. Senior Manager of Sales 18. Senior Manager of Marketing 19. Senior Manager of Operations 20. Senior Manager of Human Resources 21. Senior Manager of Research and Development 22. Senior Manager of Product Management 23. Manager of Sales 24. Manager of Marketing 25. Manager of Operations 26. Manager of Human Resources 27. Manager of Research and Development 28. Manager of Product Management 29. Sales Representative 30. Customer Service Representative",
                    "contentVector": [
                        -0.010118980892002583,
                        -0.014274303801357746,
                        ...
                        -0.03516634181141853,
                        0.013222647830843925
                    ]
                }
            ],
            "errors": null,
            "warnings": null
        }
    ]
}
```

Example Response
```json
{
    "values": [
        {
            "recordId": "r1",
            "identifiers": [
                "65630afa-0e70-43cc-b5a6-15a0ce2cb16e",
                "f4bb09c2-b60f-467b-94e1-878771f8bbf1"
            ],
            "errors": null,
            "warnings": null
        }
    ]
}
```
