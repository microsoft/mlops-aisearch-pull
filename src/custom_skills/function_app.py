import azure.functions as func
import logging
from Chunk import function_chunk
from VectorEmbed import function_vector_embed

app = func.FunctionApp()

@app.route("Health", auth_level=func.AuthLevel.ANONYMOUS)
def HealthCheck(req: func.HttpRequest) -> func.HttpResponse:
    version = 1
    logging.info(f"Health check version {version}")
    return func.HttpResponse(f"This function executed successfully with version {version}.", status_code=200)

@app.route("Chunk", auth_level=func.AuthLevel.ANONYMOUS)
def Chunk(req: func.HttpRequest) -> func.HttpResponse:
    return function_chunk(req)

@app.route("VectorEmbed", auth_level=func.AuthLevel.ANONYMOUS)
def VectorEmbed(req: func.HttpRequest) -> func.HttpResponse:
    return function_vector_embed(req)
