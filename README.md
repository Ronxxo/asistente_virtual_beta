Este es un proyecto full stack.
donde por medio del backend en python usando librerias como
from flask import Flask, request, jsonify, render_template, send_file #Importa las clases y funciones necesarias de Flask para crear una aplicación web, manejar solicitudes HTTP, devolver respuestas JSON, renderizar plantillas HTML y enviar archivos.
from openai import OpenAI #interactuar con la API de OpenAI (o OpenRouter en este caso).
import speech_recognition as sr #  para reconocer voz desde el micrófono
import time # para manejar retrasos y tiempos de espera.
from translate import Translator #de la biblioteca translate para traducir texto entre idiomas.
from gtts import gTTS#(Google Text-to-Speech) para convertir texto en audio.
import io #para manejar flujos de datos en memoria (como archivos de audio).

y esta usando el api de deepsek para responder preguntas con inteligencia artificial por voz y texto
en parte del front en el html y css y javascript se usaran msql para interactuar con la base de datos pos medio de sqlserver o pandas
