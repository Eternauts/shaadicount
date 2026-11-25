"""What we say back, in the household's language.

Fixed templates, not LLM text: the spoken number must always match the saved number.
"""

ATTENDING = {
    "hi-IN": "बहुत-बहुत धन्यवाद! हमने मेहमानों की गिनती {plates} लिख ली है{diet}। शादी में आपका इंतज़ार रहेगा!",
    "kn-IN": "ತುಂಬಾ ಧನ್ಯವಾದಗಳು! ಅತಿಥಿಗಳ ಸಂಖ್ಯೆ {plates} ಎಂದು ಬರೆದುಕೊಂಡಿದ್ದೇವೆ{diet}. ಮದುವೆಯಲ್ಲಿ ನಿಮ್ಮನ್ನು ಎದುರು ನೋಡುತ್ತೇವೆ!",
    "ta-IN": "மிக்க நன்றி! விருந்தினர் எண்ணிக்கை {plates} என்று குறித்துக்கொண்டோம்{diet}. திருமணத்தில் உங்களை எதிர்பார்க்கிறோம்!",
    "en-IN": "Thank you so much! We have noted a guest count of {plates}{diet}. We look forward to seeing you at the wedding!",
}
DECLINED = {
    "hi-IN": "बताने के लिए धन्यवाद। शादी में आपकी कमी ज़रूर महसूस होगी!",
    "kn-IN": "ತಿಳಿಸಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದಗಳು. ಮದುವೆಯಲ್ಲಿ ನಿಮ್ಮನ್ನು ಖಂಡಿತ ಮಿಸ್ ಮಾಡಿಕೊಳ್ಳುತ್ತೇವೆ!",
    "ta-IN": "தெரிவித்ததற்கு நன்றி. திருமணத்தில் உங்களை நிச்சயம் மிஸ் பண்ணுவோம்!",
    "en-IN": "Thank you for letting us know. We will miss you at the wedding!",
}
# "mixed" adds nothing: it also covers guests who did not mention food.
DIET = {
    "hi-IN": {"veg": ", और खाना शाकाहारी रहेगा", "non_veg": ", और खाना मांसाहारी रहेगा", "jain": ", और खाना जैन रहेगा"},
    "kn-IN": {"veg": ", ಊಟ ಸಸ್ಯಾಹಾರಿ", "non_veg": ", ಊಟ ಮಾಂಸಾಹಾರಿ", "jain": ", ಜೈನ ಊಟ"},
    "ta-IN": {"veg": ", சைவ உணவு", "non_veg": ", அசைவ உணவு", "jain": ", ஜெயின் உணவு"},
    "en-IN": {"veg": ", with vegetarian food", "non_veg": ", with non-vegetarian food", "jain": ", with Jain food"},
}


def confirmation(language: str, saved: dict) -> str:
    if not saved["attending"]:
        return DECLINED[language]
    return ATTENDING[language].format(
        plates=saved["headcount"] + saved["plus_ones"],
        diet=DIET[language].get(saved["diet"], ""),
    )
