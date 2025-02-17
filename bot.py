from flask import Flask, request, jsonify, render_template, send_file #Importa las clases y funciones necesarias de Flask para crear una aplicación web, manejar solicitudes HTTP, devolver respuestas JSON, renderizar plantillas HTML y enviar archivos.
from openai import OpenAI #interactuar con la API de OpenAI (o OpenRouter en este caso).
import speech_recognition as sr #  para reconocer voz desde el micrófono
import time # para manejar retrasos y tiempos de espera.
from translate import Translator #de la biblioteca translate para traducir texto entre idiomas.
from gtts import gTTS#(Google Text-to-Speech) para convertir texto en audio.
import io #para manejar flujos de datos en memoria (como archivos de audio).

app = Flask(__name__) #Crea una instancia de la aplicación Flask. __name__ es una variable especial en Python que representa el nombre del módulo actual.

class AsistenteVirtual:# definimos la clase que encapsula toda la logica del asistente
    def __init__(self): #el constructor de la clase, que se ejecuta cuando se crea una instancia de la clase.
        self.recognizer = sr.Recognizer() #Crea una instancia del reconocedor de voz.
        self.recognizer.pause_threshold = 1.0 #Establece el tiempo que el reconocedor espera antes de considerar que el usuario ha terminado de hablar.
        self.recognizer.phrase_threshold = 0.5 #Establece la sensibilidad para detectar frases.
        self.recognizer.non_speaking_duration = 0.5 #Establece el tiempo de silencio para considerar que una frase ha terminado.
        
        self.client = OpenAI( #Crea una instancia del cliente de OpenAI con la clave de API y la URL base de OpenRouter.
            api_key="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",
            base_url="https://openrouter.ai/api/v1"
        )
        
        self.translator = Translator(to_lang="es") #para traducir texto al español.
        #Define un mensaje de bienvenida que el asistente mostrará al iniciar.
        self.welcome_message = """ 
        ¡Hola! Soy tu asistente virtual. 
        Puedes hacerme cualquier pregunta o pedirme ayuda.
        Para salir, simplemente di 'salir', 'terminar' o 'adiós'.
        ¿En qué puedo ayudarte hoy?
        """
        self.max_retries = 2 #Establece el número máximo de intentos si algo falla.
        self.retry_delay = 1 #Establece el tiempo de espera entre intentos (en segundos).

    def get_ai_response(self, user_input): #Define un método para obtener una respuesta del modelo de IA.
        for attempt in range(self.max_retries): #Intenta obtener una respuesta hasta un número máximo de intentos
            try:
                chat = self.client.chat.completions.create( #Envía la solicitud al modelo de IA
                    model="deepseek/deepseek-r1:free",
                    messages=[
                        {"role": "system", "content": "Eres un asistente virtual amigable y servicial."},
                        {"role": "user", "content": user_input}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                response = chat.choices[0].message.content if chat.choices else None # Obtiene la respuesta del modelo
                if not response: #Si no hay respuesta, reintenta o devuelve un mensaje predeterminado
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return "Estoy teniendo dificultades para entender tu pregunta. ¿Podrías intentarlo de nuevo?"
                
                translated_response = self.translate_text(response) #Traduce la respuesta al español
                return translated_response #Devuelve la respuesta traducida
            except Exception as e: #Captura cualquier error durante el proceso
                print(f"Error en intento {attempt + 1}: {e}") #Muestra el error en la consola
                if attempt < self.max_retries - 1: #Si no se ha alcanzado el número máximo de intentos, reintenta.
                    time.sleep(self.retry_delay) #Espera antes de reintentar
                    continue #Continúa con el siguiente intento
                return "Disculpa, estoy teniendo problemas para procesar tu pregunta. ¿Podrías intentarlo de nuevo?" #Devuelve un mensaje de error si se agotan los intentos.

    def translate_text(self, text):
        try:
            max_length = 500 #longitud máxima de cada fragmento de texto a traducir.
            chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)] #Divide el texto en fragmentos de 500 caracteres.
            translated_chunks = [] #Inicializa una lista para almacenar los fragmentos traducidos.
            for chunk in chunks: #Itera sobre cada fragmento de texto.
                translated = self.translator.translate(chunk) #Traduce el fragmento de texto
                translated_chunks.append(translated)#Agrega el fragmento traducido a la lista
            return ' '.join(translated_chunks) #Une los fragmentos traducidos y devuelve el texto completo
        except Exception as e: #Captura cualquier error durante la traducción
            print(f"Error en traducción: {e}") #Imprime el error en la consola
            return text #Devuelve el texto original si la traducción falla

    def text_to_speech(self, text): #Define un método para convertir texto en audio

        tts = gTTS(text=text, lang='es') #Crea un objeto gTTS con el texto y el idioma español
        audio_file = io.BytesIO()#Crea un flujo de bytes en memoria para almacenar el audio
        tts.write_to_fp(audio_file) #Escribe el audio en el flujo de bytes
        audio_file.seek(0) #Reinicia el puntero del flujo de bytes al inicio
        return audio_file #Devuelve el archivo de audio

    def listen(self):#Define un método para escuchar y reconocer voz
        with sr.Microphone() as source: #Abre el micrófono como fuente de audio
            print("Escuchando...")#  Muestra un mensaje en la consola
            self.recognizer.adjust_for_ambient_noise(source, duration=1) #Ajusta el reconocedor al ruido ambiental.
            try:#Intenta reconocer la voz
                print("Puedes hablar...")
                audio = self.recognizer.listen( # Escucha el audio desde el micrófono
                    source,
                    timeout=10,
                    phrase_time_limit=10
                )
                text = self.recognizer.recognize_google(audio, language="es-ES") #Convierte el audio en texto usando la API de Google.
                print(f"Has dicho: {text}") #Muestra el texto reconocido en la consola
                return text.lower()#Devuelve el texto en minúsculas
            except sr.UnknownValueError: #Captura el error si no se puede entender el audio
                print("No se pudo entender el audio")
                return None #Devuelve None si no se puede entender el audio
            except sr.RequestError: #Captura el error si hay un problema con el servicio de reconocimiento de voz
                print("Error en el servicio de reconocimiento de voz")
                return None #Devuelve None si hay un error en el servicio
            except sr.WaitTimeoutError: #Captura el error si se agota el tiempo de espera
                print("Tiempo de espera agotado")
                return None

# Creamos una instancia del asistente virtual
asistente = AsistenteVirtual()

# Ruta principal para la interfaz web
@app.route('/')
def index(): #Define la función que se ejecuta cuando se accede a la ruta principal
    return render_template('index.html') #Renderiza la plantilla index.html

# Ruta para manejar las solicitudes de texto
@app.route('/chat', methods=['POST']) #Define la ruta para manejar solicitudes de texto
def chat(): #Define la función que se ejecuta cuando se recibe una solicitud POST en /chat
    data = request.json #Obtiene los datos JSON de la solicitud
    user_input = data.get('mensaje') #Obtiene el mensaje del usuario
    
    if user_input.lower() in ["salir", "terminar", "adiós"]: # Si el usuario quiere salir, devuelve un mensaje de despedida.
        return jsonify({
            'respuesta': "¡Hasta luego! Que tengas un excelente día.",
            'audio_url': '/audio?text=¡Hasta luego! Que tengas un excelente día.'
        })
    
    response = asistente.get_ai_response(user_input) # Obtiene la respuesta del asistente
    audio_url = f'/audio?text={response}'#Genera la URL para el archivo de audio.
    return jsonify({'respuesta': response, 'audio_url': audio_url})#Devuelve la respuesta y la URL del audio en formato JSON.

# Ruta para manejar las solicitudes de voz
@app.route('/chat_voz', methods=['POST']) # Define la ruta para manejar solicitudes de voz.
def chat_voz():#Define la función que se ejecuta cuando se recibe una solicitud POST en /chat_voz
    try:#Intenta procesar la solicitud de voz
        user_input = asistente.listen()  # Escuchamos al usuario obteniendo el texto reconocido
        if not user_input: #Si no se entendió el audio, devuelve un mensaje de error
            return jsonify({
                'respuesta': "No te he entendido, ¿puedes repetirlo?",
                'audio_url': '/audio?text=No te he entendido, ¿puedes repetirlo?'
            })
        
        if user_input.lower() in ["salir", "terminar", "adiós"]: #Si el usuario quiere salir, devuelve un mensaje de despedida
            return jsonify({
                'respuesta': "¡Hasta luego! Que tengas un excelente día.",
                'audio_url': '/audio?text=¡Hasta luego! Que tengas un excelente día.'
            })
        
        response = asistente.get_ai_response(user_input)# Obtiene la respuesta del asistente
        audio_url = f'/audio?text={response}'#Genera la URL para el archivo de audio.
        return jsonify({'respuesta': response, 'audio_url': audio_url}) #Devuelve la respuesta y la URL del audio en formato JSON.
    except Exception as e: #Captura cualquier error durante el proceso
        print(f"Error en chat_voz: {e}")
        return jsonify({ #Devuelve un mensaje de error en formato JSON.
            'respuesta': "Hubo un error al procesar tu solicitud de voz.",
            'audio_url': '/audio?text=Hubo un error al procesar tu solicitud de voz.'
        })

# Ruta para generar audio
@app.route('/audio')#Define la ruta para generar audio
def audio():# Define la función que se ejecuta cuando se accede a la ruta /audio
    text = request.args.get('text') #Obtiene el texto a convertir en audio desde los parámetros de la URL.
    audio_file = asistente.text_to_speech(text) #Convierte el texto en audio
    return send_file(audio_file, mimetype='audio/mp3') #Devuelve el archivo de audio como respuesta

if __name__ == '__main__':#Verifica si el script se está ejecutando directamente
    app.run(debug=True)#Inicia la aplicación Flask en modo de depuración