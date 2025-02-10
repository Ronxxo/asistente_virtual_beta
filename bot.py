# Importamos las bibliotecas necesarias
from openai import OpenAI        # Para interactuar con modelos de IA
import pyttsx3                   # Motor de síntesis de voz (text-to-speech)
import speech_recognition as sr  # Para reconocimiento de voz
import time                      # Para manejar delays y tiempos de espera
from translate import Translator # Para traducir texto entre idiomas

class AsistenteVirtual:
    def __init__(self):
        # Constructor de la clase - aquí inicializamos todo lo que necesitamos
        
        # Inicializar motor de voz - esto crea una instancia del sintetizador
        self.engine = pyttsx3.init()
        
        # Buscamos una voz en español entre las disponibles en el sistema
        # Útil para que suene más natural en nuestro idioma
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "spanish" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        # Configuración del reconocedor de voz
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.0        # Tiempo que espera antes de considerar que terminamos de hablar
        self.recognizer.phrase_threshold = 0.5       # Sensibilidad para detectar frases
        self.recognizer.non_speaking_duration = 0.5  # Tiempo de silencio para considerar que terminó una frase
        
        # Configuración de la API de OpenAI
        # Nota: La API key es específica para OpenRouter, un servicio que da acceso a varios modelos
        self.client = OpenAI(
            api_key="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",
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Inicializar el traductor - lo configuramos para que traduzca todo a español
        self.translator = Translator(to_lang="es")
        
        # Mensaje que se muestra al iniciar el programa
        # Las triples comillas permiten strings multilínea en Python
        self.welcome_message = """
        ¡Hola! Soy tu asistente virtual. 
        Puedes hacerme cualquier pregunta o pedirme ayuda.
        Para salir, simplemente di 'salir', 'terminar' o 'adiós'.
        ¿En qué puedo ayudarte hoy?
        """

        # Variables para el sistema de reintentos
        self.max_retries = 2     # Número máximo de intentos si algo falla
        self.retry_delay = 1     # Segundos que espera entre intentos

    def translate_text(self, text):
        # Método para traducir texto a español
        try:
            # Dividimos el texto en pedazos de 500 caracteres
            # Esto es necesario porque la API gratuita tiene límites de longitud
            max_length = 500
            chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
            
            # Traducimos cada pedazo por separado
            translated_chunks = []
            for chunk in chunks:
                translated = self.translator.translate(chunk)
                translated_chunks.append(translated)
            
            # Unimos todos los pedazos traducidos
            return ' '.join(translated_chunks)
        except Exception as e:
            print(f"Error en traducción: {e}")
            return text  # Si falla la traducción, devolvemos el texto original

    def speak(self, text):
        # Método para convertir texto a voz
        self.engine.say(text)           # Agregamos el texto a la cola de reproducción
        self.engine.runAndWait()        # Reproducimos todo lo que está en la cola

    def listen(self):
        # Método para escuchar y reconocer voz
        with sr.Microphone() as source:  # Usamos el micrófono como fuente de audio
            print("Escuchando...")
            # Ajustamos el reconocedor al ruido ambiental
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            try:
                print("Puedes hablar...")
                # Grabamos el audio
                audio = self.recognizer.listen(
                    source,
                    timeout=10,          # Tiempo máximo que espera antes de empezar a grabar
                    phrase_time_limit=10 # Tiempo máximo de grabación
                )
                
                # Convertimos el audio a texto usando la API de Google
                text = self.recognizer.recognize_google(audio, language="es-ES")
                print(f"Has dicho: {text}")
                return text.lower()      # Devolvemos el texto en minúsculas
            except sr.UnknownValueError:
                print("No se pudo entender el audio")
                return None
            except sr.RequestError:
                print("Error en el servicio de reconocimiento de voz")
                return None
            except sr.WaitTimeoutError:
                print("Tiempo de espera agotado")
                return None

    def get_ai_response(self, user_input):
        # Método para obtener respuesta del modelo de IA
        for attempt in range(self.max_retries):
            try:
                # Hacemos la petición al modelo de IA
                chat = self.client.chat.completions.create(
                    model="deepseek/deepseek-r1:free",  # Modelo gratuito de DeepSeek
                    messages=[
                        # Le damos contexto al modelo sobre su rol
                        {"role": "system", "content": "Eres un asistente virtual amigable y servicial."},
                        # Le enviamos la pregunta del usuario
                        {"role": "user", "content": user_input}
                    ],
                    max_tokens=150,      # Limitamos la longitud de la respuesta
                    temperature=0.7      # Control de creatividad/aleatoriedad (0-1)
                )
                
                # Extraemos la respuesta del modelo
                response = chat.choices[0].message.content if chat.choices else None
                
                # Verificamos si obtuvimos una respuesta
                if not response:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return "Lo siento, no pude generar una respuesta. ¿Podrías reformular tu pregunta?"
                
                # Traducimos la respuesta al español
                translated_response = self.translate_text(response)
                return translated_response
                
            except Exception as e:
                print(f"Error en intento {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return "Disculpa, estoy teniendo problemas para procesar tu pregunta. ¿Podrías intentarlo de nuevo?"

    def run(self):
        # Método principal que ejecuta el asistente
        print(self.welcome_message)
        self.speak(self.welcome_message)

        # Bucle principal del programa
        while True:
            user_input = self.listen()   # Escuchamos al usuario
            
            # Si no entendimos lo que dijo
            if not user_input:
                self.speak("No te he entendido, ¿puedes repetirlo?")
                continue
            
            # Si el usuario quiere salir    
            if user_input in ["salir", "terminar", "adiós"]:
                self.speak("¡Hasta luego! Que tengas un excelente día.")
                break

            # Procesamos la pregunta y obtenemos respuesta
            response = self.get_ai_response(user_input)
            print(f"Respuesta: {response}")
            self.speak(response)

# Punto de entrada del programa
if __name__ == "__main__":
    asistente = AsistenteVirtual()  # Creamos una instancia del asistente
    asistente.run()                 # Iniciamos el asistente