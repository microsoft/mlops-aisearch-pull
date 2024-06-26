import json
import os
from unittest.mock import patch, mock_open, MagicMock
from azure.storage.blob import BlobServiceClient
from custom_skills.Chunk import _get_request_schema, _chunk_pdf_file_from_azure2, REQUEST_SCHEMA_PATH

def test_get_request_schema():
    mock_schema = {
            "recordID": "test string!",
            "data": {
                    "filename": "test_file.pdf",
                    "minLength": 1000000
                }
            }
    
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_schema))) as mock_file:
        result = _get_request_schema()
        mock_file.assert_called_once_with(REQUEST_SCHEMA_PATH)

        assert result == mock_schema 
  
def test__chunk_pdf_file_from_azure2():    
    mock_file_name = "test_file.pdf"    
    mock_chunk_size = 1000    
    mock_overlap_size = 100    
    mock_chunks = ['chunk1', 'chunk2', 'chunk3']    
    
    os.environ["AZURE_STORAGE_ACCOUNT_CONNECTION_STRING"] = "test_conn_string"    
    os.environ["AZURE_STORAGE_CONTAINER_NAME"] = "test_container"    
  
    with patch('azure.storage.blob.BlobServiceClient.from_connection_string', return_value=MagicMock()) as mock_from_conn_string:    
        with patch('builtins.open', mock_open()) as mock_file:    
            with patch('langchain.document_loaders.PyPDFLoader') as MockPyPDFLoader:    
                with patch('langchain.text_splitter.RecursiveCharacterTextSplitter') as MockTextSplitter:    
  
                    mock_blob_service = mock_from_conn_string.return_value  
                    mock_container_client = MagicMock()    
                    mock_blob_service.get_container_client.return_value = mock_container_client    
                    mock_blob_client = MagicMock()    
                    mock_container_client.get_blob_client.return_value = mock_blob_client    
  
                    mock_loader = MockPyPDFLoader.return_value
  
                    mock_splitter = MockTextSplitter.return_value    
                    mock_splitter.split_documents.return_value = mock_chunks    
  
                    result = _chunk_pdf_file_from_azure2(    
                        mock_file_name,     
                        mock_chunk_size,     
                        mock_overlap_size    
                    )    
  
                    mock_from_conn_string.assert_called_once_with("test_conn_string")    
                    mock_container_client.get_blob_client.assert_called_once_with(blob=mock_file_name)    
  
                    mock_file.assert_called_once_with(f"/tmp/{mock_file_name}", "wb")    
                    MockPyPDFLoader.assert_called_once_with(f"/tmp/{mock_file_name}")
  
                    MockTextSplitter.assert_called_once_with(chunk_size=mock_chunk_size, chunk_overlap=mock_overlap_size)    
  
                    assert result == mock_chunks  

