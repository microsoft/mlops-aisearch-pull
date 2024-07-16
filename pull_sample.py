from dotenv import load_dotenv
from mlops.common.config_utils import MLOpsConfig
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient 
from azure.search.documents.models import (
    QueryType,
    QueryCaptionType,
    QueryAnswerType
)
from azure.search.documents import SearchClient, SearchItemPaged
from azure.search.documents.models import VectorizableTextQuery
from azure.search.documents.indexes.models import (
    SearchIndexer,
    FieldMapping
)

from azure.search.documents.indexes.models import (
    SplitSkill,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    AzureOpenAIEmbeddingSkill,
    SearchIndexerIndexProjections,
    SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjectionsParameters,
    IndexProjectionMode,
    SearchIndexerSkillset,
    WebApiSkill,
)
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndexerDataContainer,
    SearchIndexerDataSourceConnection
)
from azure.search.documents.indexes._generated.models import NativeBlobSoftDeleteDeletionDetectionPolicy
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    HnswParameters,
    VectorSearchAlgorithmMetric,
    ExhaustiveKnnAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIParameters,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
    SearchIndex
)
import os



# Connect to Blob Storage and upload documents
def upload_documents(blob_connection_string, blob_container_name):
    """upload documents from the data folder to the blob container"""
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client(blob_container_name)
    if not container_client.exists():
        container_client.create_container()

    documents_directory = os.path.join("data")
    for file in os.listdir(documents_directory):
        with open(os.path.join(documents_directory, file), "rb") as data:
            name = os.path.basename(file)
            if not container_client.get_blob_client(name).exists():
                container_client.upload_blob(name=name, data=data)

    print(f"Documents are uploaded to {blob_container_name}")

def create_datasource(indexer_client, blob_container_name, blob_connection_string, index_name):
    """Create a data source connection to the blob container"""
    container = SearchIndexerDataContainer(name=blob_container_name)
    data_source_connection = SearchIndexerDataSourceConnection(
        name=f"{index_name}-blob",
        type="azureblob",
        connection_string=blob_connection_string,
        container=container,
        data_deletion_detection_policy=NativeBlobSoftDeleteDeletionDetectionPolicy()
    )
    data_source = indexer_client.create_or_update_data_source_connection(data_source_connection)

    print(f"Data source '{data_source.name}' created or updated")
    return data_source

def create_search_index(index_client, index_name, azure_openai_endpoint, azure_openai_key, azure_openai_embedding_deployment ):
    """Create a search index with vector search and semantic search configurations""" 
    fields = [  
        SearchField(name="parent_id", type=SearchFieldDataType.String, sortable=True, filterable=True, facetable=True),  
        SearchField(name="title", type=SearchFieldDataType.String),  
        SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True, analyzer_name="keyword"),  
        SearchField(name="chunk", type=SearchFieldDataType.String, sortable=False, filterable=False, facetable=False),  
        SearchField(name="vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),  
    ]  
  
    # Configure the vector search configuration  
    vector_search = VectorSearch(  
        algorithms=[  
            HnswAlgorithmConfiguration(  
                name="myHnsw",  
                parameters=HnswParameters(  
                    m=4,  
                    ef_construction=400,  
                    ef_search=500,  
                    metric=VectorSearchAlgorithmMetric.COSINE,  
                ),  
            ),  
            ExhaustiveKnnAlgorithmConfiguration(  
                name="myExhaustiveKnn",  
                parameters=ExhaustiveKnnParameters(  
                    metric=VectorSearchAlgorithmMetric.COSINE,  
                ),  
            ),  
        ],  
        profiles=[  
            VectorSearchProfile(  
                name="myHnswProfile",  
                algorithm_configuration_name="myHnsw",  
                vectorizer="myOpenAI",  
            ),  
            VectorSearchProfile(  
                name="myExhaustiveKnnProfile",  
                algorithm_configuration_name="myExhaustiveKnn",  
                vectorizer="myOpenAI",  
            ),  
        ],  
        
        vectorizers=[  
            AzureOpenAIVectorizer(  
                name="myOpenAI",  
                kind="azureOpenAI",  
                azure_open_ai_parameters=AzureOpenAIParameters(  
                    resource_uri=azure_openai_endpoint,  
                    deployment_id=azure_openai_embedding_deployment,  
                    api_key=azure_openai_key,  
                ),  
            ),  
        ],  
    )  
  
    semantic_config = SemanticConfiguration(  
        name="my-semantic-config",  
        prioritized_fields=SemanticPrioritizedFields(  
            content_fields=[SemanticField(field_name="chunk")]  
        ),  
    )  
  
    # Create the semantic search with the configuration  
    semantic_search = SemanticSearch(configurations=[semantic_config])  
  
    # Create the search index
    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search, semantic_search=semantic_search)  
    result = index_client.create_or_update_index(index)  
    print(f"{result.name} created")  
    return index




def create_skillset(indexer_client, index_name, azure_openai_endpoint, azure_openai_key, azure_openai_embedding_deployment):
    """Create a skillset with split and embedding skills"""  
    skillset_name = f"{index_name}-skillset"  
  
    split_skill = SplitSkill(  
        description="Split skill to chunk documents",  
        text_split_mode="pages",  
        context="/document",  
        maximum_page_length=2000,  
        page_overlap_length=500,  
        inputs=[  
            InputFieldMappingEntry(name="text", source="/document/content"),  
        ],  
        outputs=[  
            OutputFieldMappingEntry(name="textItems", target_name="pages")  
        ],  
    )  
  
    embedding_skill = AzureOpenAIEmbeddingSkill(  
        description="Skill to generate embeddings via Azure OpenAI",  
        context="/document/pages/*",  
        resource_uri=azure_openai_endpoint,  
        deployment_id=azure_openai_embedding_deployment,  
        api_key=azure_openai_key,  
        inputs=[  
            InputFieldMappingEntry(name="text", source="/document/pages/*"),  
        ],  
        outputs=[  
            OutputFieldMappingEntry(name="embedding", target_name="vector")  
        ],  
    )  
  
    index_projections = SearchIndexerIndexProjections(  
        selectors=[  
            SearchIndexerIndexProjectionSelector(  
                target_index_name=index_name,  
                parent_key_field_name="parent_id",  
                source_context="/document/pages/*",  
                mappings=[  
                    InputFieldMappingEntry(name="chunk", source="/document/pages/*"),  
                    InputFieldMappingEntry(name="vector", source="/document/pages/*/vector"),  
                    InputFieldMappingEntry(name="title", source="/document/metadata_storage_name"),  
                ],  
            ),  
        ],  
        parameters=SearchIndexerIndexProjectionsParameters(  
            projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS  
        ),  
    )  
  
    skillset = SearchIndexerSkillset(  
        name=skillset_name,  
        description="Skillset to chunk documents and generating embeddings",  
        skills=[split_skill, embedding_skill],  
        index_projections=index_projections,  
    )  
   
    indexer_client.create_or_update_skillset(skillset)  
    print(f"{skillset.name} created")  
    return skillset_name


def create_indexer(indexer_client, index_name, skillset_name, data_source):
    """# Create an indexer to index documents and generate embeddings""" 
    indexer_name = f"{index_name}-indexer"  
  
    indexer = SearchIndexer(  
        name=indexer_name,  
        description="Indexer to index documents and generate embeddings",  
        skillset_name=skillset_name,  
        target_index_name=index_name,  
        data_source_name=data_source.name,  
        # Map the metadata_storage_name field to the title field in the index to display the PDF title in the search results  
        field_mappings=[FieldMapping(source_field_name="metadata_storage_name", target_field_name="title")]  
    )  
  
    indexer_result = indexer_client.create_or_update_indexer(indexer)  
  
    # Run the indexer  
    indexer_client.run_indexer(indexer_name)  
    print(f' {indexer_name} is created and running. If queries return no results, please wait a bit and try again.')  

def run_indexer(indexer_client, indexer_name):
    """Run the indexer to index documents and generate embeddings on demand"""
    indexer_client.run_indexer(indexer_name)
    print(f' {indexer_name} is running. If queries return no results, please wait a bit and try again.')


def run_vector_search(query, search_client):
    """Run a pure vector search for a given query"""
    
    vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=1, fields="vector", exhaustive=True)
    # Use the below query to pass in the raw vector query instead of the query vectorization
    # vector_query = RawVectorQuery(vector=generate_embeddings(query), k_nearest_neighbors=3, fields="vector")
  
    results = search_client.search(  
        search_text=None,  
        vector_queries= [vector_query],
        select=["parent_id", "chunk_id", "chunk"],
        top=1
    )  
  
    for result in results:  
        print(f"parent_id: {result['parent_id']}")  
        print(f"chunk_id: {result['chunk_id']}")  
        print(f"Score: {result['@search.score']}")  
        print(f"Content: {result['chunk']}")   

def run_hybrid_search(query, search_client):
    """Run a hybrid search for a given query"""
    vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=1, fields="vector", exhaustive=True)
  
    results = search_client.search(  
        search_text=query,  
        vector_queries= [vector_query],
        select=["parent_id", "chunk_id", "chunk"],
        top=1
    )  
  
    for result in results:  
        print(f"parent_id: {result['parent_id']}")  
        print(f"chunk_id: {result['chunk_id']}")  
        print(f"Score: {result['@search.score']}")  
        print(f"Content: {result['chunk']}")


def run_hybridsearch_semanticranking(query, search_client):
    """Run a hybrid search with semantic ranking for a given query"""
    vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=1, fields="vector", exhaustive=True)

    results = search_client.search(  
        search_text=query,
        vector_queries=[vector_query],
        select=["parent_id", "chunk_id", "chunk"],
        query_type=QueryType.SEMANTIC,
        semantic_configuration_name='my-semantic-config',
        query_caption=QueryCaptionType.EXTRACTIVE,
        query_answer=QueryAnswerType.EXTRACTIVE,
        top=1
    )

    semantic_answers = results.get_answers()
    if semantic_answers:
        for answer in semantic_answers:
            if answer.highlights:
                print(f"Semantic Answer: {answer.highlights}")
            else:
                print(f"Semantic Answer: {answer.text}")
            print(f"Semantic Answer Score: {answer.score}\n")

    for result in results:
        print(f"parent_id: {result['parent_id']}")  
        print(f"chunk_id: {result['chunk_id']}")  
        print(f"Reranker Score: {result['@search.reranker_score']}")
        print(f"Content: {result['chunk']}")  

        captions = result["@search.captions"]
        if captions:
            caption = captions[0]
            if caption.highlights:
                print(f"Caption: {caption.highlights}\n")
            else:
                print(f"Caption: {caption.text}\n")



def run_driver():
    mlops_config = MLOpsConfig()

    # Variables not used here do not need to be updated in your .env file
    endpoint = mlops_config.acs_config['acs_api_base']
    credential = mlops_config.acs_config['acs_api_key']
    credential = AzureKeyCredential(mlops_config.acs_config['acs_api_key'])

    index_name = mlops_config.acs_config['acs_index_name']
    blob_connection_string = mlops_config.sub_config['storage_account_connection_string']
    blob_container_name = mlops_config.sub_config['storage_container_name']
    azure_openai_endpoint = mlops_config.aoai_config['aoai_api_base']
    azure_openai_key = mlops_config.aoai_config['aoai_api_key']
    azure_openai_embedding_deployment = mlops_config.aoai_config['aoai_embedding_model_deployment']


    indexer_client = SearchIndexerClient(endpoint, credential)
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
    search_client = SearchClient(endpoint, index_name, credential=credential)
    # query = "What plans offer coverage for routine physicals, well-child visits, immunizations"
  
    # upload_documents(blob_connection_string, blob_container_name)
    # datasource = create_datasource(indexer_client=indexer_client, blob_connection_string=blob_connection_string, blob_container_name=blob_container_name, 
    #                                index_name=index_name)
    # index = create_search_index(index_client=index_client, 
    #                             index_name=index_name,
    #                             azure_openai_endpoint=azure_openai_endpoint,
    #                             azure_openai_key=azure_openai_key,
    #                             azure_openai_embedding_deployment=azure_openai_embedding_deployment)
    
    # skillset_name = create_skillset(indexer_client=indexer_client, index_name=index_name, 
    #                 azure_openai_endpoint=azure_openai_endpoint,
    #                 azure_openai_key=azure_openai_key,
    #                 azure_openai_embedding_deployment=azure_openai_embedding_deployment)
    # create_indexer(indexer_client=indexer_client, index_name=index_name, skillset_name= skillset_name , data_source= datasource)
    # run_indexer(indexer_client=indexer_client, indexer_name=f"{index_name}-indexer")
   
    query = "who is responsible for technical direction at contoso electronics"
    # print("pure vector search")
    # print("query: ", query)
    # run_vector_search(query=query, search_client=search_client)
    # print("hybrid search")
    # run_hybrid_search(query=query, search_client=search_client)
    print("hybrid search with semantic ranker")
    run_hybridsearch_semanticranking(query=query, search_client=search_client)
 
if __name__ == "__main__":
    run_driver()