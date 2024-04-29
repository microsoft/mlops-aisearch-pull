"""Azure Function App for custom skills."""
import azure.functions as func
import logging
from Chunk import function_chunk
from VectorEmbed import function_vector_embed

app = func.FunctionApp()


@app.route("Health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Check health of the function."""
    version = 1
    logging.info(f"Health check version {version}")
    return func.HttpResponse(f"This function executed successfully with version {version}.", status_code=200)


@app.route("Chunk", auth_level=func.AuthLevel.ANONYMOUS)
def chunk(req: func.HttpRequest) -> func.HttpResponse:
    """Divide document into chunks of text."""
    return function_chunk(req)


@app.route("VectorEmbed", auth_level=func.AuthLevel.ANONYMOUS)
def vector_embed(req: func.HttpRequest) -> func.HttpResponse:
    """Convert text to vector embedding."""
    return function_vector_embed(req)
