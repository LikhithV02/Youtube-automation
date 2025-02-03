from kokoro import KPipeline
from pathlib import Path
import soundfile as sf
import numpy as np
import os

pipeline = KPipeline(lang_code='a')

def generate_audio(prompt: str, output_path: str):
     # Create the output directory if it doesn't exist
    output_dir = Path(output_path).parent
    os.makedirs(output_dir, exist_ok=True)
    
    generator = pipeline(
        prompt, voice='af_heart', speed=1, split_pattern=r'\n+'
    )
    
    all_audio = []  # List to hold all audio segments
    
    for i, (gs, ps, audio) in enumerate(generator):
        # Save individual audio segment
        # audio_path = Path(output_path) / f"output_{i}.wav"
        # sf.write(str(audio_path), audio, 24000)  # Explicitly convert Path to string
        
        # Collect audio for combining
        all_audio.append(audio)
    
    # Combine all audio segments into one file
    if all_audio:
        combined_audio = np.concatenate(all_audio)
        combined_path = Path(output_path)
        sf.write(str(combined_path), combined_audio, 24000)

if __name__ == '__main__':
    generate_audio('''
The sky above the port was the color of television, tuned to a dead channel.
"It's not like I'm using," Case heard someone say, as he shouldered his way through the crowd around the door of the Chat. "It's like my body's developed this massive drug deficiency."
It was a Sprawl voice and a Sprawl joke. The Chatsubo was a bar for professional expatriates; you could drink there for a week and never hear two words in Japanese.

These were to have an enormous impact, not only because they were associated with Constantine, but also because, as in so many other areas, the decisions taken by Constantine (or in his name) were to have great significance for centuries to come. One of the main issues was the shape that Christian churches were to take, since there was not, apparently, a tradition of monumental church buildings when Constantine decided to help the Christian church build a series of truly spectacular structures. The main form that these churches took was that of the basilica, a multipurpose rectangular structure, based ultimately on the earlier Greek stoa, which could be found in most of the great cities of the empire. Christianity, unlike classical polytheism, needed a large interior space for the celebration of its religious services, and the basilica aptly filled that need. We naturally do not know the degree to which the emperor was involved in the design of new churches, but it is tempting to connect this with the secular basilica that Constantine completed in the Roman forum (the so-called Basilica of Maxentius) and the one he probably built in Trier, in connection with his residence in the city at a time when he was still caesar.

[Kokoro](/kˈOkəɹO/) is an open-weight TTS model with 82 million parameters. Despite its lightweight architecture, it delivers comparable quality to larger models while being significantly faster and more cost-efficient. With Apache-licensed weights, [Kokoro](/kˈOkəɹO/) can be deployed anywhere from production environments to personal projects.
''', "output")