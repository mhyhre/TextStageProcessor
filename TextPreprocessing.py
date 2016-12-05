#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import codecs
import math

from pymorphy2 import tokenizers 

from TextData import TextData



# Читает текст из файла и возвращает список предложений (без запятых)
def readSentencesFromInputText(filename, input_dir_name):

    with codecs.open(input_dir_name + '/' + filename, 'r', "utf-8") as text_file:
        data=text_file.read().replace('\n', ' ')
        sentences = data.split('.')
        for i in range(len(sentences)):
            sentences[i] = sentences[i].strip().replace(',', '')
        return sentences
    return None

# Загружает из директории input_dir_name все txt файлы в список объектов TextData
def loadInputFiles(input_dir_name):
    input_filenames = []
    for filename in os.listdir(input_dir_name):
        if filename.endswith(".txt"):
            input_filenames.append(filename);

    texts = []
    for filename in input_filenames:
        text_data = TextData(filename)
        text_data.original_sentences = readSentencesFromInputText(filename, input_dir_name)
        texts.append(text_data)

    return texts

def tokenizeTextData(texts):
    # Переводим предложения в списки слов (tokenized_sentence)
    for text in texts:
        for sentence in text.original_sentences:
            if(len(sentence) > 0):
                tokenized_sentence = tokenizers.simple_word_tokenize(sentence)
                text.tokenized_sentences.append(tokenized_sentence)
    return texts





# Записывает/перезаписывает строку любой длины c переносами (data_str) в файл (filename)
def writeStringToFile(data_str, filename):
    with open(filename, 'w') as out_text_file:
        out_text_file.write(data_str)

# Определяет является ли слово частью ФИО (с вероятностью score)
def wordPersonDetector(word, morph):
    results = morph.parse(word)
    for result in results:
        if('Name' in result.tag
                or 'Surn' in result.tag
                or 'Patr' in result.tag):
            if(result.score >= 0.05):
                return True
    return False

# Удаляет СТОП-СЛОВа (Предлоги, союзы и тд.)
def removeStopWordsFromSentences(sentences, morph):
    for sentence in sentences:
        i = 0
        while i < len(sentence):
            current_word = sentence[i]

            if(len(current_word) < 3):
                 sentence.pop(i)
                 i = i - 1
            else:
                results = morph.parse(current_word)
                for result in results:
                    if(result.tag.POS == 'ADJF'
                        or result.tag.POS == 'ADJS'
                        or result.tag.POS == 'PREP'
                        or result.tag.POS == 'ADVB'
                        or result.tag.POS == 'COMP'
                        or result.tag.POS == 'CONJ'
                        or result.tag.POS == 'PRCL'):
                        if(result.score >= 0.25):
                            sentence.pop(i)
                            i = i - 1
                            break
            i = i + 1
    return sentences

# Проверяет является ли слово местоимением-существительным (Он, Она и тд.)
def wordPersonNPRODetector(word, morph):
    results = morph.parse(word)
    for result in results:
        if(result.tag.POS == 'NPRO'):
            if(result.score >= 0.2):
                return True
    return False

# Заменяет ОН, ОНА и тд. на последнюю упомянутую персону в предложении.
def deanonimizeSentence(updated_sentence, deanon_stack, morph):
    result_sentence = []
    for word in updated_sentence:
        if(wordPersonNPRODetector(word, morph) and len(deanon_stack)>0):
            result_sentence.append(deanon_stack[-1][0])
        else:
            result_sentence.append(word)

    return result_sentence


# Извлекает из текста наиболее большие группы слов из sentence в которых
# поддержка каждого слова не менее чем minimalSupport, а группа не менее чем из minimalSize слов
def formFrequencySet(words_dict, sentence, minimal_support, minimal_size):
    words_in_sentence = len(sentence)
    result_groups = []

    # Составляем последовательности начиная с каждого слова
    for word_index in range(words_in_sentence):
        word_group = []
        for i in range(word_index, words_in_sentence):
            current_word = sentence[i]
            if(current_word == '"' or current_word == "'"):
                continue
            else:
                if(words_dict.get(current_word, 0) >= minimal_support):
                    word_group.append(current_word)
                else:
                    break

        if(len(word_group) >= minimal_size):
            result_groups.append(word_group)

    return result_groups


# Вычисляет поддерку групп слов в списке
def calculateGroupsSupport(group_list):
    result_dict = dict()

    for group in group_list:
        key = ''
        for word in group:
            key = key + ' ' + word
        key = key[1:]
        result_dict[key] = result_dict.get(key, 0) + 1
        
    return result_dict



def isSentencesContainsWord(sentences, test_word):
    for sentence in sentences:
        for word in sentence:
            if(str(word) == str(test_word)):
                return True
    return False

def count_of_words_in_sentences(sentences):
    counter = 0
    for sentence in sentences:
        for word in sentence:
            counter = counter + 1
    return counter

# Вычисляет IDF для каждого слова каждого текста и возвращает словарик СЛОВО:IDF
def calculateWordsIDF(texts, ):
    all_documents_count = len(texts);
    idf_data = dict()
    for text in texts:
        for word, frequency in text.word_frequency.items():
            word_doc_freq = 0.0;

            for doc in texts:
                if(isSentencesContainsWord(doc.register_pass_centences, word)):
                    word_doc_freq = word_doc_freq + 1.0
                    continue

            pre_idx = (0.0 + all_documents_count)/word_doc_freq
            inverse_document_frequency = math.log10(pre_idx)
            idf_data[word] = inverse_document_frequency
    return idf_data


# Вычисляет TF*IDF для каждого слова каждого текста и записывает в text.words_tf_idf[word]
def calculateTFIDF(texts, idf_word_data):
    for text in texts:
        text.word_count = count_of_words_in_sentences(text.register_pass_centences)
        for word, frequency in text.word_frequency.items():
            tf = frequency/text.word_count
            text.words_tf_idf[word] = idf_word_data[word] * tf;

def writeWordTFIDFToString(texts, idf_word_data):
    log_string = "Файлы\n"
    for text in texts:
        log_string = log_string + "\n" + text.filename + ";;;;"+'\n'
        log_string = log_string + 'Word; IDF; TF; IDF*TF;\n'

        for word, frequency in text.word_frequency.items():
            tf = frequency/text.word_count
            log_string = log_string + word + ";" + str(idf_word_data[word]) + ';' + str(tf) + ';' + str(text.words_tf_idf[word])  + ';\n'
    return log_string


def removeTFIDFWordsWithMiniamlMultiplier(texts , min_mult):
    for text in texts:
        sorted_TFIDF = sorted(text.words_tf_idf.items(), key=lambda x: x[1], reverse=True)  
        max_value = 0.0
        if(len(sorted_TFIDF)>0):
            max_value = sorted_TFIDF[0][1]

        minimal_value = min_mult*max_value
        for item in sorted_TFIDF:
            word = item[0]
            tfidf = item[1]
            
            if(tfidf < minimal_value):
                text.words_tf_idf.pop(word)
                text.word_frequency.pop(word)