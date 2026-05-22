import google.generativeai as genai

genai.configure(api_key="AIzaSyApKQofNhyf8nRKPT1D3rfruQR_oaeYrbs")

for model in genai.list_models():
    print(model.name)