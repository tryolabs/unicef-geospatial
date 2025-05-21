from llama_index.core import Document, VectorStoreIndex
from utils.constants import CCRI_METADATA_FILENAME, CCRI_METADATA_PERSIST_DIR


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
