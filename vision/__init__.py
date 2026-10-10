"""Vision Module Exports"""
from vision.capture import FaceCapture
from vision.age_api import ThirdPartyAgeService

try:
    from vision.embeddings import FaceEmbeddings
    __all__ = ['FaceCapture', 'FaceEmbeddings', 'ThirdPartyAgeService']
except ImportError:
    __all__ = ['FaceCapture', 'ThirdPartyAgeService']