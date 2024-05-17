from dependencies import *

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        # get every page in a pdf
        for page in pdf_reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text
    return text

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200, 
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks):
    if not text_chunks:
        raise ValueError("No text chunks to process for embeddings.")
    embeddings = OpenAIEmbeddings()
    #embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def get_converstation_chain(vectorstore):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key= 'chat_history', return_messages=True)
    converstation_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=vectorstore.as_retriever(), memory=memory)
    
    return converstation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation(user_question)
    st.session_state.chat_history = response['chat_history']
    #st.write(response)
    
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
            
def show_chat_page():
    # Tạo tiêu đề
    st.set_page_config(page_title="Chat with multiple PDFs", page_icon=":books:")
    st.write(css, unsafe_allow_html=True)
    
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
    
    st.header("Chat with multiple PDFs :books:")
    
    if st.button("Go to Home Page"):
        st.session_state.current_page = "Home"
        st.rerun()
    
    user_question = st.text_input("Ask a question about your documents:") 
    if user_question:
        handle_userinput(user_question)
    
    with st.sidebar:
        st.sidebar.title("Your documents")
        pdf_docs = st.file_uploader("Upload your PDFs", type=["pdf"], accept_multiple_files=True) 
        if st.button("Process"):
            if pdf_docs:
                with st.spinner("Processing..."):
                        # get pdf text
                        raw_text = get_pdf_text(pdf_docs)
                        if not raw_text:
                            st.error("No text could be extracted from the uploaded PDFs.")
                            return
                        
                        # get chunk text
                        text_chunks = get_text_chunks(raw_text)
                        if not text_chunks:
                            st.error("No text chunks could be created from the extracted text.")
                            return
                        
                        # create a vector store
                        vectorstore = get_vectorstore(text_chunks)
                        st.success("Vector store created successfully!")
                        
                        #create a conversation chain
                        st.session_state.conversation = get_converstation_chain(vectorstore)
            else:
                st.error("Please upload at least one PDF file.")
