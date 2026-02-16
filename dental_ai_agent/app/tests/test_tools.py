import google.generativeai as genai
genai.configure(api_key="AIzaSyA1a-gOUxz92BPljCjtZymXg91LcmOsjIo")

for m in genai.list_models():
    print(m.name)
