from dict import chat_dict, symptom_to_disease, lang, keyword_urls
from flask import Flask, render_template, request, jsonify
import requests
import webbrowser
from translate import Translator
from bs4 import BeautifulSoup
from datetime import datetime
import time

app = Flask(__name__)

last_user_activity = time.time()
reminder_sent1 = False
reminder_sent2 = False
REMINDER_INTERVAL = 15
NO_RESPONSE_INTERVAL = 30
conversation_history = []

def open_webpage(url):
    webbrowser.open(url)

def filter_text(text):
    result = "".join(char for char in text if char.isalnum() or char.isspace())
    return result

def search_google(query):
    url = f"https://www.google.com/search?q={query}"
    req = requests.get(url)
    soup = BeautifulSoup(req.text, "html.parser")
    search_result = soup.find("div", class_="BNeawe").text
    return search_result

def get_possible_disease(symptoms):
    possible_diseases = set()
    for symptom in symptoms:
        if symptom in symptom_to_disease:
            possible_diseases.update(symptom_to_disease[symptom])
    return list(possible_diseases)

def translate_text(text, target_language):
    translator = Translator(from_lang='en', to_lang=lang.get(target_language.lower()))
    sentences = text.split('. ')
    translated_sentences = []
    for sentence in sentences:
        translation = translator.translate(sentence)
        translated_sentences.append(translation)
    translated_text = '. '.join(translated_sentences)
    return translated_text
 
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global last_user_activity, reminder_sent1, reminder_sent2

    user_message = request.form.get('user_message')
    last_user_activity = time.time()
    user_input = request.form['user_message'].lower()
    user_input = filter_text(user_input)
    response = ""
    reminder_sent1 = False
    reminder_sent2 = False
    user_symptoms = []  
    try:
        if user_input == 'bye':
            response = "Durgss: Goodbye!"
        elif user_input.startswith('translate'):
            translation_input = user_input.replace('translate', '').strip()
            translation_parts = translation_input.split('to')
            if len(translation_parts) == 2:
                text_to_translate = translation_parts[0].strip()
                target_language = translation_parts[1].strip()
                translated_text = translate_text(text_to_translate, target_language)
                response = f"Durgss: Translated text: {translated_text}"
            else:
                response = "Durgss: Invalid translation request. Please provide a text to translate and a target language."
        elif user_input in chat_dict:
            response = "Durgss: " + chat_dict[user_input]
        else:
            for symptom_keyword in symptom_to_disease:
                if symptom_keyword in user_input:
                    user_symptoms.append(symptom_keyword)

            if not user_symptoms:
                for keyword, url in keyword_urls.items():
                    if keyword in user_input:
                        open_webpage(url)
                        response += "\nDurgss: Opening... "
                        break

            if user_symptoms:
                possible_diseases = get_possible_disease(user_symptoms)

                if possible_diseases:
                    response += "\nDurgss: Possible diseases based on your symptoms:\n"
                    for disease in possible_diseases:
                        response += "- " + disease + "\n"
                else:
                    response += "\nDurgss: No specific disease could be identified based on the symptoms provided."
            
            if not response:
                search_result = search_google(user_input)
                response = "Durgss: " + search_result
                reminder_sent = False
    except Exception as e:
        app.logger.error(f"Error occurred: {e}")
        response = "Durgss: Oops! Something went wrong. Please try again later."

    return jsonify({'message': response})

@app.route('/check_activity')
def check_activity():
    global last_user_activity, reminder_sent1, reminder_sent2, REMINDER_INTERVAL, NO_RESPONSE_INTERVAL

    current_time = time.time()
    time_since_activity = current_time - last_user_activity
    
    reminder_condition = time_since_activity >= REMINDER_INTERVAL and not reminder_sent1
    no_response_condition = time_since_activity >= NO_RESPONSE_INTERVAL and not reminder_sent2

    if reminder_condition:
        reminder_message = "Durgss: Hey, are you there?"
        response = {'message': reminder_message}
        reminder_sent1 = True
    elif no_response_condition:
        reminder_message = "Durgss: Hello, can you hear me? Please type something. I'm waiting for your response."
        response = {'message': reminder_message}
        reminder_sent2 = True
      
    else:
        # If there has been recent activity, send an empty response
        response = {'message': ''}

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
  chat_dict = {
        'hi': 'hello!',
        'hello': 'Hi there!',
        'hey': 'Hey!',
        'greetings': 'Greetings!',
        'good morning': 'Good morning!',
        'good afternoon': 'Good afternoon!',
        'good evening': 'Good evening!',
        'howdy': 'Howdy!',
        'nice to meet you': 'Nice to meet you!',
        'welcome': 'Welcome!',
        'how are you': 'I am doing well, thank you.',
        'I need help': 'Sure, what can I help you with?',
        'what is your name': 'My name is Durgss.',
        'what can you do': 'I can answer your questions and chat with you.',
        'what is the weather like today': 'I am sorry, I do not have access to weather information.',
        'do you have any siblings': 'No, I am an only chatbot.',
        'tell me a joke': 'Why did the tomato turn red? Because it saw the salad dressing!',
        'what is the meaning of life': 'That is a difficult question. What do you think the meaning of life is?',
        'who created you': 'I was created by TOXIC BOYS.',
        'what is your favorite color': 'As an AI, I do not have a favorite color.',
        'can you recommend a good book': 'What kind of book are you interested in?',
        'what is your favorite movie': 'I do not watch movies as I am an AI program.',
        'how do I reset my password': 'You will need to contact your service provider or visit their website to reset your password.',
        'what is your favorite food': 'As an AI, I do not have a favorite food.',
        'what is your favorite hobby': 'As an AI, I do not have hobbies. However, I do enjoy helping people.',
        'what is the meaning of love': 'Love is a complex emotion that can mean different things to different people.',
        'can you play a game with me': 'I am sorry, I am not capable of playing games at this time.',
        'i love you': 'Sorry! I am single and I am young',
        'yes':'oh! i am scared',
        'its nice':'eee :) thank you',
        'nice':'Thank you :)',
        'you are so cute':"Hey don't make me blush",
        'i hate you': 'ha ha ha dont worry',
        'good morning':'good morning',
        'good night':'Have a sweet dreams,good night'
}

symptom_to_disease = {
    "fever": ["common cold", "influenza", "malaria", "COVID-19", "typhoid"],
    "cough": ["common cold", "pneumonia", "bronchitis", "COVID-19", "tuberculosis"],
    "headache": ["migraine", "tension headache", "sinusitis", "meningitis", "concussion"],
    "fatigue": ["anemia", "chronic fatigue syndrome", "hypothyroidism", "fibromyalgia"],
    "abdominal pain": ["gastroenteritis", "appendicitis", "gastric ulcer", "kidney stones"],
    "shortness of breath": ["asthma", "pneumonia", "chronic obstructive pulmonary disease (COPD)"],
    "chest pain": ["angina", "heart attack", "acid reflux", "pulmonary embolism"],
    "sore throat": ["tonsillitis", "strep throat", "mononucleosis"],
    "rash": ["allergic reaction", "eczema", "psoriasis", "measles"],
    "joint pain": ["osteoarthritis", "rheumatoid arthritis", "gout", "fibromyalgia"],
    "nausea": ["motion sickness", "food poisoning", "viral gastroenteritis"],
    "vomiting": ["gastroenteritis", "food poisoning", "stomach flu"],
    "diarrhea": ["gastroenteritis", "food poisoning", "irritable bowel syndrome (IBS)"],
    "dizziness": ["vertigo", "inner ear infection", "low blood pressure"],
    "frequent urination": ["urinary tract infection (UTI)", "diabetes", "overactive bladder"],
    "painful urination": ["urinary tract infection (UTI)", "bladder stones", "sexually transmitted infections (STIs)"],
    "lower abdominal pain": ["appendicitis", "ovarian cysts", "endometriosis"],
}

lang = {
    'afrikaans': 'af', 'albanian': 'sq', 'amharic': 'am', 'arabic': 'ar', 'armenian': 'hy', 'azerbaijani': 'az',
    'basque': 'eu', 'belarusian': 'be', 'bengali': 'bn', 'bosnian': 'bs', 'bulgarian': 'bg', 'catalan': 'ca',
    'cebuano': 'ceb', 'chichewa': 'ny', 'chinese (simplified)': 'zh-CN', 'chinese (traditional)': 'zh-TW',
    'corsican': 'co', 'croatian': 'hr', 'czech': 'cs', 'danish': 'da', 'dutch': 'nl', 'english': 'en',
    'esperanto': 'eo', 'estonian': 'et', 'filipino': 'tl', 'finnish': 'fi', 'french': 'fr', 'frisian': 'fy',
    'galician': 'gl', 'georgian': 'ka', 'german': 'de', 'greek': 'el', 'gujarati': 'gu', 'haitian creole': 'ht',
    'hausa': 'ha', 'hawaiian': 'haw', 'hebrew': 'iw', 'hindi': 'hi', 'hmong': 'hmn', 'hungarian': 'hu',
    'icelandic': 'is', 'igbo': 'ig', 'indonesian': 'id', 'irish': 'ga', 'italian': 'it', 'japanese': 'ja',
    'javanese': 'jw', 'kannada': 'kn', 'kazakh': 'kk', 'khmer': 'km', 'korean': 'ko', 'kurdish (kurmanji)': 'ku',
    'kyrgyz': 'ky', 'lao': 'lo', 'latin': 'la', 'latvian': 'lv', 'lithuanian': 'lt', 'luxembourgish': 'lb',
    'macedonian': 'mk', 'malagasy': 'mg', 'malay': 'ms', 'malayalam': 'ml', 'maltese': 'mt', 'maori': 'mi',
    'marathi': 'mr', 'mongolian': 'mn', 'myanmar (burmese)': 'my', 'nepali': 'ne', 'norwegian': 'no', 'odia': 'or',
    'pashto': 'ps', 'persian': 'fa', 'polish': 'pl', 'portuguese': 'pt', 'punjabi': 'pa', 'romanian': 'ro',
    'russian': 'ru', 'samoan': 'sm', 'scots gaelic': 'gd', 'serbian': 'sr', 'sesotho': 'st', 'shona': 'sn',
    'sindhi': 'sd', 'sinhala': 'si', 'slovak': 'sk', 'slovenian': 'sl', 'somali': 'so', 'spanish': 'es',
    'sundanese': 'su', 'swahili': 'sw', 'swedish': 'sv', 'tajik': 'tg', 'tamil': 'ta', 'telugu': 'te',
    'thai': 'th', 'turkish': 'tr', 'ukrainian': 'uk', 'urdu': 'ur', 'uyghur': 'ug', 'uzbek': 'uz',
    'vietnamese': 'vi', 'welsh': 'cy', 'xhosa': 'xh', 'yiddish': 'yi', 'yoruba': 'yo', 'zulu': 'zu'
}

keyword_urls = {
    "book a train ticket": "https://www.irctc.co.in/",
    "book train ticket": "https://www.irctc.co.in/",
    "whatsapp":"https://web.whatsapp.com/",
    "facebook":"https://www.facebook.com/",
    "instagram":"https://www.instagram.com/",
    "shop": "https://www.amazon.in/",
    "amazon": "https://www.amazon.in/",
    "flipkart": "https://www.flipkart.com/",
    "irctc": "https://www.irctc.co.in/",
    "gpt": "https://chat.openai.com/",
    "spotify":"https://open.spotify.com/",
    "youtube":"https://www.youtube.com/",
    "utube":"https://www.youtube.com/"
    }
