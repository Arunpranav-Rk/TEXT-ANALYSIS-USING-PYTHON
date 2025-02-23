import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from textblob import TextBlob
from nltk.corpus import cmudict
from nltk.tokenize import word_tokenize, sent_tokenize
import nltk

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('cmudict')

# Load the CMU Pronouncing Dictionary for syllable count
cmu_dict = cmudict.dict()

def count_syllables(word):
    word = word.lower()
    if word in cmu_dict:
        return max([len(list(y for y in x if y[-1].isdigit())) for x in cmu_dict[word]])
    return 1

def count_complex_words(words):
    return sum(1 for word in words if count_syllables(word) > 2)

def extract_metrics(text, positive_words, negative_words):
    # Tokenize sentences and words
    sentences = sent_tokenize(text)
    words = word_tokenize(text)
    
    # Word count
    word_count = len(words)
    
    # Complex word count
    complex_word_count = count_complex_words(words)
    
    # Positive and Negative Scores
    positive_score = sum(1 for word in words if word.lower() in positive_words)
    negative_score = sum(1 for word in words if word.lower() in negative_words)

    # Polarity and Subjectivity
    blob = TextBlob(text)
    polarity_score = blob.sentiment.polarity
    subjectivity_score = blob.sentiment.subjectivity

    # Readability Metrics
    avg_sentence_length = word_count / len(sentences)
    percentage_complex_words = (complex_word_count / word_count) * 100
    fog_index = 0.4 * (avg_sentence_length + percentage_complex_words)

    # Average words per sentence
    avg_words_per_sentence = word_count / len(sentences)

    # Syllables per word
    syllables_per_word = sum(count_syllables(word) for word in words) / word_count

    # Personal pronouns
    personal_pronouns = len([word for word, pos in nltk.pos_tag(words) if pos in ('PRP', 'PRP$')])

    # Average word length
    avg_word_length = sum(len(word) for word in words) / word_count

    return {
        "Positive Score": positive_score,
        "Negative Score": negative_score,
        "Polarity Score": polarity_score,
        "Subjectivity Score": subjectivity_score,
        "Avg Sentence Length": avg_sentence_length,
        "Percentage of Complex Words": percentage_complex_words,
        "Fog Index": fog_index,
        "Avg Words per Sentence": avg_words_per_sentence,
        "Complex Word Count": complex_word_count,
        "Word Count": word_count,
        "Syllables per Word": syllables_per_word,
        "Personal Pronouns": personal_pronouns,
        "Avg Word Length": avg_word_length
    }

def main(input_file, output_file, positive_words_file, negative_words_file):
    # Load input Excel file
    df = pd.read_excel(input_file)
    
    # Load positive and negative word lists
    with open(positive_words_file, 'r') as file:
        positive_words = set(file.read().splitlines())
    with open(negative_words_file, 'r') as file:
        negative_words = set(file.read().splitlines())

    # Initialize output data
    output_data = []

    for _, row in df.iterrows():
        try:
            response = requests.get(row['URL'])
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()

            metrics = extract_metrics(text, positive_words, negative_words)
            metrics['URL_ID'] = row['URL_ID']
            metrics['URL'] = row['URL']

            output_data.append(metrics)
        except Exception as e:
            print(f"Error processing URL {row['URL']}: {e}")

    # Create output DataFrame
    output_df = pd.DataFrame(output_data)

    # Save to Excel
    output_df.to_excel(output_file, index=False)

if __name__ == "__main__":
    input_file = "./input/Input.xlsx"  # Replace with your input file path
    output_file = "./output/Output.xlsx"  # Replace with your desired output file path
    positive_words_file = "./positive-words.txt"  # Replace with the positive words file path
    negative_words_file = "./negative-words.txt"  # Replace with the negative words file path
    main(input_file, output_file, positive_words_file, negative_words_file)
    
    