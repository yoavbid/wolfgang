import faiss
import pickle
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import TextLoader



def generate_similarity_index():
    data_files_list= list((simply_tutor_path / "training_data/").glob("**/*.srt"))
    data_files_list.extend(list((simply_tutor_path / "training_data/").glob("**/*.txt")))

    documents = []
    for data_file in data_files_list:
        loader = TextLoader(data_file)
        documents.extend(loader.load())
        
    textSplitter = CharacterTextSplitter(chunk_size=2000, separator="\n")

    docs = textSplitter.split_documents(documents)

    store = FAISS.from_documents(docs, OpenAIEmbeddings())
    # faiss.write_index(store.index, str(simply_tutor_path / "training_data" / "app_context.index"))
    
    # docs = store.similarity_search("middle c")

    # with open(simply_tutor_path / "training_data" / "faiss.pkl", "wb") as f:
    #     pickle.dump(store, f)
        
    store.save_local(simply_tutor_path / "faiss_index")
    
def load_similarity_index():
    store = FAISS.load_local("faiss_index", OpenAIEmbeddings())
        
    return store


def test_similarity_index(text):
    index = faiss.read_index(str(simply_tutor_path / "training_data" / "app_context.index"))

    with open(simply_tutor_path / "training_data" / "faiss.pkl", "rb") as f:
        store = pickle.load(f)

    store.index = index

    docs = store.similarity_search(text, k=3) #similarity_search(text)
    for i, doc in enumerate(docs):
        print('%d. ' % i, doc.page_content, '\n\n')
        
        
def main():
    generate_similarity_index()
    
    test_similarity_index('What other songs can I practice after Somewhere Over the Rainbow?')
    
        
if __name__ == "__main__":
    main()