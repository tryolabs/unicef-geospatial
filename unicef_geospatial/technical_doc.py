from llama_index.core import (
    Document,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.retrievers import VectorIndexRetriever
from utils.constants import (
    CCRI_METADATA_FILENAME,
    CCRI_METADATA_PERSIST_DIR,
)


def get_ccri_metadata(query: str) -> str:
    """Get the metadata for the CCRI dataset.

    The documentation contains detailed information about the CCRI methodology,
    data sources, and technical specifications for the Climate Change Risk Index.

    This function uses a vector index to search the CCRI technical documentation.
    It returns the most relevant information from the documentation based on the query.

    Args:
        query: The query to search the CCRI technical documentation.

    Returns:
        The most relevant chunks from the CCRI technical documentation as a string.
    """
    vector_index = load_index_from_storage(
        StorageContext.from_defaults(persist_dir=CCRI_METADATA_PERSIST_DIR)
    )

    retriever = VectorIndexRetriever(
        index=vector_index,
        similarity_top_k=5,
    )

    response = retriever.retrieve(query)
    return "\n".join([r.text for r in response])


def process_ccri_doc():
    with open(CCRI_METADATA_FILENAME, "r") as f:
        text = f.read()

    documents = [Document(text=text)]

    vector_index = VectorStoreIndex.from_documents(documents)
    query_engine = vector_index.as_query_engine()

    response = query_engine.query("What is the CCRI?")

    vector_index.storage_context.persist(CCRI_METADATA_PERSIST_DIR)

    print(response)


if __name__ == "__main__":
    process_ccri_doc()
