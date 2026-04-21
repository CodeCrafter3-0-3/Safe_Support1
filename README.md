# Safe_Support1
Haven is a dual-layered safety and support ecosystem designed for women facing domestic abuse.

Problem Statement
Globally, 1 in 3 women experiences physical or sexual violence in her lifetime, often by an intimate partner. In India, 30% of women have faced domestic violence at least once (WHO, National Family Health Survey). Abusers often control and monitor digital communications, isolating these women and preventing them from safely reaching out for help.

Haven’s Solution 💪
Discreet SOS Messaging through Steganography
Women in abusive relationships are often unable to directly call out for help. Social media profiles and call histories are under constant surveillance by their abuser, making it difficult to seek assistance openly.
Our Solution: Haven utilizes steganography to encode discreet distress messages within seemingly innocent images, allowing women to communicate in plain sight, without arousing suspicion.

AI Avatar for Mental Health Support
Many survivors endure their struggles in silence, with only 10% seeking mental health support.
Our Solution: A compassionate AI chatbot provides confidential support, offering personalized coping strategies and resources, especially important as women experiencing abuse are 80% more likely to face mental health challenges.

Law Bot with Knowledge of Legal Rights
In India, only 14% of women have access to formal legal support. Haven’s Law Bot helps change this by providing instant, confidential guidance on abuse cases, custody battles, and property claims.
Our Solution: Trained on the Indian constitution and other legal documents, the bot helps women gain the confidence to advocate for their rights, making legal support accessible to all.

Detailed Description 📝
1. Discreet SOS Messaging through Steganography
For many women in abusive relationships who live under constant monitoring, finding a way to ask for help without alerting their abusers is critical. Haven introduces a revolutionary SOS messaging system, using steganography to encode distress signals within innocent-looking images, like flowers or landscapes.

How it Works 🛠️
On the user side, Haven’s process begins with message generation, where the user enters brief details of their situation. Our LLM expands these inputs into complete, coherent sentences. The user then chooses an image prompt, like a flower or landscape, which the AI generates and encodes with the distress message through steganography. Once complete, the user shares this seemingly ordinary image on social media, where it appears innocuous to others, including any abusers monitoring the profile.

On the authority side, Haven's system continuously monitors social media for SOS images tagged with specific hashtags. Once detected, these images are decoded to extract the hidden message using reverse steganography. The decoded text is then broken down into structured segments for efficient analysis, after which it is stored in MongoDB, where cases are organized by severity level to prioritize urgent responses.

