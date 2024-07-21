from transformers import pipeline, RobertaTokenizer, RobertaForQuestionAnswering, T5Tokenizer, T5ForConditionalGeneration
from transformers import BertTokenizer, BertForQuestionAnswering, DistilBertTokenizer, DistilBertForQuestionAnswering
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import preprocess as pp
import streamlit as st
    
def model(question, context):
    
    lemmatizer = WordNetLemmatizer()
    q = word_tokenize(question)
    q = [i.lower() for i in q]
    q = [lemmatizer.lemmatize(i) for i in q]
    
    if  q[0] == 'summarise' or q[0] == 'summarize':
        return T5(context), 'summarizer'
    else:
         return roberta(question, context), 'question_answering'

## LLM for Summarisation
def T5(context):
    tokenizer = T5Tokenizer.from_pretrained("Falconsai/text_summarization")
    model = T5ForConditionalGeneration.from_pretrained("Falconsai/text_summarization")

    nlp = pipeline('summarization', model=model, tokenizer=tokenizer)
    
    context = pp.get_text_chunks(context)
    
    res = nlp(context, max_length=150, min_length=30, do_sample=False) 
    
    return res

## LLM for Question Answering
def roberta(question, context):
    try:
        model_name = RobertaForQuestionAnswering.from_pretrained("deepset/roberta-base-squad2")
        tokenizer = RobertaTokenizer.from_pretrained("deepset/roberta-base-squad2")
        
        nlp = pipeline('question-answering', model=model_name, tokenizer=tokenizer)
        QA_input = {
            'question': question,
            'context': context
        }
        res = nlp(QA_input)

        return res
    except Exception as e:
        st.error(f"An error occurred during model loading: {e}")
        return None

def bert_model(question, context):
    
    tokenizer = BertTokenizer.from_pretrained("google-bert/bert-base-uncased")
    model_name = BertForQuestionAnswering.from_pretrained("google-bert/bert-base-uncased")

    nlp = pipeline('question-answering', model=model_name, tokenizer=tokenizer)
    QA_input = {
        'question': question,
        'context': context
    }
    res = nlp(QA_input) 
    
    return res

def distillBert_model(question, context):
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-cased-distilled-squad')
    model_name = DistilBertForQuestionAnswering.from_pretrained('distilbert-base-cased-distilled-squad')
    
    nlp = pipeline('question-answering', model=model_name, tokenizer=tokenizer)
   
    QA_input = {
        'question': question,
        'context': context
    }
    
    res = nlp(QA_input) 
    
    return res