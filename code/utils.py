import jieba
import numpy as np
import os
from collections import Counter
from keras.preprocessing.sequence import pad_sequences
import re
import random
import gensim
from collections import OrderedDict
from gensim.models import word2vec


def getEmbeddingMatrix(word_index, EMBEDDING_DIM):
    GLOVE_DIR = "/ext/home/analyst/Testground/data/glove"
    embeddings_index = {}
    f = open(os.path.join(GLOVE_DIR, 'glove.6B.100d.txt'))
    for line in f:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        embeddings_index[word] = coefs
    f.close()
    print('Total %s word vectors in Glove 6B 100d.' % len(embeddings_index))

    embedding_matrix = np.random.random((len(word_index) + 1, EMBEDDING_DIM))
    for word, i in word_index.items():
        embedding_vector = embeddings_index.get(word)
        if embedding_vector is not None:
            # words not found in embedding index will be all-zeros.
            embedding_matrix[i] = embedding_vector
    return embeddings_index


def is_ustr(instr):
    out_str = ''
    for index in range(len(instr)):
        if u'\u4e00' <= instr[index] <= u'\u9fff':
            out_str = out_str + instr[index].strip()
        elif instr[index].isdigit():
            a = 1
        elif instr[index].isalnum():
            a =1
        elif instr[index].isalpha():
            a = 1
        elif instr[index] == '%' or instr[index] == '℃' or instr[index] == '.':
            a = 1
        else:
            return False
    return True


def getNotCoveredData(trainCorpusPath, testCorpusPath,trainSinglePath,testSinglePath,intersectionPath, topN, dict_file,
                      stop_words_file, car_list_file, digit_list_file, fraction_list_file, distance_list_file,
                      money_list_file, city_list_file):
    jieba.load_userdict(dict_file)

    stop_words = []
    stop_words_text = open(stop_words_file, 'r', encoding='utf8')
    for line in stop_words_text.readlines():
        stop_words.append(line.encode('utf-8').decode('utf-8-sig').strip().upper())
    stop_words.append(' ')

    train = open(trainCorpusPath, 'r', encoding='utf8')
    test = open(testCorpusPath,'r',encoding='utf8')
    trainSingle = open(trainSinglePath,'w',encoding='utf8')
    testSigle = open(testSinglePath,'w',encoding='utf8')
    intersection = open(intersectionPath,'w',encoding='utf8')

    train.readline()
    test.readline()

    train_words = []
    for line in train.readlines():
        line = line.strip().split('\t')
        text = line[1].replace(" ", "").upper()
        for word in jieba.cut(text, cut_all=False, HMM=True):
            if word not in stop_words:
                if is_ustr(word):
                    train_words.append(word)
                # else:
                #     print(word)

    c = Counter(train_words).most_common(topN)  # 找出出现次数最多的topN个单词
    trainWordDict = {}
    for item in c:
        trainWordDict[str(item[0])] = str(item[1])

    test_words = []
    for line in test.readlines():
        line = line.strip().split(',')
        text = line[1].replace(" ", "").upper()
        for word in jieba.cut(text, cut_all=False, HMM=True):
            if word not in stop_words:
                if is_ustr(word):
                    test_words.append(word)
                # else:
                #     print(word)

    c_test = Counter(test_words).most_common(topN)
    testWordDict = {}
    for item in c_test:
        testWordDict[str(item[0])] = str(item[1])

    trainSingle.write('word\tcnt\n')
    testSigle.write('word\tcnt\n')
    intersection.write('word\ttrain_cnt\ttest_cnt\n')
    index = 1
    # train_index = 1
    # test_index = 1
    for word in testWordDict:
        if(word not in trainWordDict):
            intersection.write(word + ',' + str(0) + '|' + testWordDict[word] + ',' + str(index) + '\n')
            index += 1
            # if int(testWordDict[word]) > 1:
            #     intersection.write(word + ',' + str(0) + '|' + testWordDict[word] + ',' + str(index) + '\n')
            #     index += 1
            # else:
            #     testSigle.write(word + '\t' + testWordDict[word] + ',' + str(test_index) + '\n')
            #     test_index += 1
        else:
            intersection.write(word + ',' + trainWordDict[word] + '|' + testWordDict[word] + ',' + str(index) + '\n')
            index += 1

    for word in trainWordDict:
        if(word not in testWordDict):
            intersection.write(word + ',' + trainWordDict[word] + '|' + str(0) + ',' + str(index) + '\n')
            index += 1
            # if int(trainWordDict[word]) > 1:
            #     intersection.write(word + ',' + trainWordDict[word] + '|' + str(0) + ',' + str(index) + '\n')
            #     index += 1
            # else:
            #     trainSingle.write(word + '\t' + trainWordDict[word] + ',' + str(train_index) + '\n')
            #     train_index += 1
    print(index)
    train.close()
    test.close()
    trainSingle.close()
    testSigle.close()
    intersection.close()


##################################################### 预测 #############################################################
def getPredict(model, test_file, test_predict_file, max_sequence_length, word2id, car_list, dict_file, digit_list,
               fraction_list, distance_list, money_list, city_list):
    test = open(test_file, 'r', encoding='utf8')
    o = open(test_predict_file, 'w', encoding='utf8')
    o_arr = open('../result/oridata.txt', 'w', encoding='utf8')
    contentId = []
    test_X = []
    test.readline()
    jieba.load_userdict(dict_file)
    for line in test.readlines():
        line = line.strip().split(',')
        curSequence = getSequenceId(line[1], word2id, car_list, digit_list, fraction_list, distance_list, money_list,
                                    city_list, shuffle=False, drop=False)
        contentId.append(line[0])
        test_X.append(curSequence)  # 用于存储转换成id的文本
    test.close()

    test_X = pad_sequences(test_X, maxlen=max_sequence_length, padding='post', truncating='post',
                           value=0.)  # 固定句子最大长度，在末尾处补0或截断
    predictArr = model.predict(test_X, batch_size=128)  # 返回预测值的numpy array

    for i in predictArr:
        o_arr.write(str(i))
    o_arr.close()

    predict = {}
    for i in range(len(predictArr)):
        for j in range(len(predictArr[0])):
            if predictArr[i][j] > 0.9:
                if i not in predict:
                    predict[i] = [j]
                else:
                    predict[i].append(j)
    for i in range(len(predictArr)):
        if i not in predict:
            predict[i] = [np.argmax(predictArr[i])]

    o.write("content_id,subject,sentiment_value,sentiment_word\n")  # 写入标题
    for i in range(len(contentId)):  # 对文本id遍历
        for label in predict[i]:
            predictCate, predictSentiment = decode10Cate(label)  # 对类别进行解码
            o.write(contentId[i]+','+predictCate+','+str(predictSentiment)+','+'\n')  # 写入预测
    o.close()


def getSentiPredict(model, test_file, test_predict_file, max_sequence_length, word2id, car_list):
    test = open(test_file, 'r', encoding='utf8')
    o = open(test_predict_file, 'w', encoding='utf8')
    contentId = []
    test_X = []
    test_X_CATE_ONE_HOT = []
    test_X_CATE = []
    test.readline()
    for line in test.readlines():
        line = line.strip().split(',')
        curSequence = getSequenceId(line[1], word2id, car_list)
        contentId.append(line[0])
        test_X_CATE.append(line[2].strip())
        cateFeature = getOneHotLabel(encode10Cate(line[2].strip()), 10)  ## 10 is the subject number
        test_X.append(curSequence)  #
        test_X_CATE_ONE_HOT.append(cateFeature)
    test.close()

    test_X = pad_sequences(test_X, maxlen=max_sequence_length, padding='post', truncating='post',value=0.)
    test_X_CATE_ONE_HOT = np.array(test_X_CATE_ONE_HOT,dtype=np.float32)
    predictArr = model.predict([test_X, test_X_CATE_ONE_HOT], batch_size=128)  # 返回预测值的numpy array
    predictArr = np.argmax(predictArr, axis=-1)

    for i in range(len(contentId)):
        if i == 0:
            o.write("content_id,subject,sentiment_value,sentiment_word\n")
        o.write(contentId[i]+','+test_X_CATE[i]+','+str(int(predictArr[i])-1)+','+'\n')
    o.close()


########################################## batch生成器###################3 #################################
def batch_iter(data_size, x_data, y_data, batch_size, num_epochs, shuffle=True):
    """
    Generates a batch iterator for a dataset.
    """
    # data_size = len(data)
    num_batches_per_epoch = int((data_size-1)/batch_size) + 1
    for epoch in range(num_epochs):
        if shuffle:  # Shuffle the data at each epoch
            shuffle_indices = np.random.permutation(np.arange(data_size))
            shuffled_data_x = x_data[shuffle_indices]
            shuffled_data_y = y_data[shuffle_indices]
        else:
            shuffled_data_x = x_data
            shuffled_data_y = y_data
        for batch_num in range(num_batches_per_epoch):
            start_index = batch_num * batch_size
            end_index = min((batch_num + 1) * batch_size, data_size)
            yield (shuffled_data_x[start_index:end_index], shuffled_data_y[start_index:end_index])


def senti_batch_iter(data_size, x_data,x_data_cate, y_data, batch_size, num_epochs, shuffle=True):
    num_batches_per_epoch = int((data_size - 1) / batch_size) + 1
    for epoch in range(num_epochs):
        if shuffle:  # Shuffle the data at each epoch
            shuffle_indices = np.random.permutation(np.arange(data_size))
            shuffled_data_x = x_data[shuffle_indices]
            shuffled_data_y = y_data[shuffle_indices]
            shuffled_data_x_cate = x_data_cate[shuffle_indices]
        else:
            shuffled_data_x = x_data
            shuffled_data_y = y_data
            shuffled_data_x_cate = x_data_cate
        for batch_num in range(num_batches_per_epoch):
            start_index = batch_num * batch_size  # 开始索引
            end_index = min((batch_num + 1) * batch_size, data_size)  # 最后索引，解决最后一个batch溢出的问题
            yield (shuffled_data_x[start_index:end_index], shuffled_data_y[start_index:end_index], shuffled_data_x_cate[start_index:end_index])


########################################### 获取word的id(文本，word+id) ################################################
def getSequenceId(sequence, word2id, car_list, digit_list, fraction_list, distance_list, money_list, city_list, shuffle, drop):
    sequenceId = []
    for word in jieba.cut(sequence.upper(), cut_all=False, HMM=True):
        if word in word2id:
            sequenceId.append(int(word2id[word]))
    if drop:
        len_s = len(sequenceId)
        delen = int(len_s * 0.2)
        for i in range(delen):
            a = random.uniform(0, len_s-1)
            sequenceId.pop(round(a))
            len_s = len_s - 1
    if shuffle:
        random.shuffle(sequenceId)
    # print(len(sequenceId))
    # lens = len(sequenceId)
    return sequenceId


####################################################### 泛化类 #########################################################
def getList(car_list_file, digit_list_file, fraction_list_file, distance_list_file, money_list_file, city_list_file):
    car_list = []
    carListFile = open(car_list_file, 'r', encoding='utf8')
    for line in carListFile.readlines():
        car_list.append(line.encode('utf-8').decode('utf-8-sig').strip().upper())

    digit_list = []
    digitListFile = open(digit_list_file, 'r', encoding='utf8')
    for line in digitListFile.readlines():
        digit_list.append(line.encode('utf-8').decode('utf-8-sig').strip().upper())
    digitListFile.close()

    fraction_list = []
    fractionListFile = open(fraction_list_file, 'r', encoding='utf8')
    for line in fractionListFile.readlines():
        fraction_list.append(line.encode('utf-8').decode('utf-8-sig').strip().upper())
    fractionListFile.close()

    distance_list = []
    distanceListFile = open(distance_list_file, 'r', encoding='utf8')
    for line in distanceListFile.readlines():
        distance_list.append(line.encode('utf-8').decode('utf-8-sig').strip().upper())
    distanceListFile.close()

    money_list = []
    moneyListFile = open(money_list_file, 'r', encoding='utf8')
    for line in moneyListFile.readlines():
        money_list.append(line.encode('utf-8').decode('utf-8-sig').strip().upper())
    moneyListFile.close()

    city_list = []
    cityListFile = open(city_list_file, 'r', encoding='utf8')
    for line in cityListFile.readlines():
        city_list.append(line.encode('utf-8').decode('utf-8-sig').strip().upper())
    cityListFile.close()

    return car_list, digit_list, fraction_list, distance_list, money_list, city_list


####################################################### 语料库 #########################################################
def getYuliao(w2v_result_file, yuliao_file, car_list_file, digit_list_file, fraction_list_file, distance_list_file,
              money_list_file, city_list_file):

    car_list, digit_list, fraction_list, distance_list, \
    money_list, city_list = getList(car_list_file, digit_list_file, fraction_list_file,
                                    distance_list_file, money_list_file, city_list_file)

    w2v_result = open(w2v_result_file, 'r', encoding='utf8')
    yuliao=[[]]
    yuliao_line = []
    for line in w2v_result.readlines():
        line = line.strip().split(' ')
        for word in line:
            if word in car_list:
                yuliao_line.append('汽车汽车1')
            elif all(char.isdigit() for char in word):
                yuliao_line.append('数字数字2')
            elif re.match(re.compile(r"^(-?\d+)(\.\d*)?$"), word) and float(word) <= 4.0:
                yuliao_line.append('动力小数3')
            elif re.match(re.compile(r"^(-?\d+)(\.\d*)?$"), word):
                yuliao_line.append('油耗小数4')
            elif word in digit_list:
                yuliao_line.append('数字文字5')
            elif word in fraction_list:
                yuliao_line.append('百分文字6')
            elif word in distance_list:
                yuliao_line.append('距离文字7')
            elif word in money_list:
                yuliao_line.append('金钱文字8')
            elif word in city_list:
                yuliao_line.append('地点文字9')
            else:
                yuliao_line.append(word)
        yuliao.append(yuliao_line)
        yuliao_line=[]
    yuliao_doc = open(yuliao_file, 'w', encoding='utf8')
    for line in yuliao:
        for i in range(len(line)):
            if i == len(line)-1:
                yuliao_doc.write(line[i] + '\n')
            else:
                yuliao_doc.write(line[i] + ' ')
    w2v_result.close()
    yuliao_doc.close()


########################################################## wordvec #####################################################
def get_w2v_model(w2v_data_file, w2v_result_file, yuliao_file, dict_file, w2v_model, embedding_size, car_list_file,
                  digit_list_file, fraction_list_file, distance_list_file, money_list_file, city_list_file):
    w2v_data=open(w2v_data_file, 'r', encoding='utf8')
    document = w2v_data.read()
    jieba.load_userdict(dict_file)
    document_cut = jieba.cut(document, cut_all=False)
    result = ' '.join(document_cut)
    w2v_result = open(w2v_result_file, 'w', encoding='utf8')
    w2v_result.write(result)
    getYuliao(w2v_result_file, yuliao_file, car_list_file, digit_list_file, fraction_list_file, distance_list_file,
              money_list_file, city_list_file)
    sentences = word2vec.Text8Corpus(yuliao_file)
    w2v_data.close()
    w2v_result.close()
    # sentences = word2vec.Text8Corpus(w2v_result_file)
    model = word2vec.Word2Vec(sentences, size=embedding_size)
    model.save(w2v_model)



def get_word_vector(word2id, w2v_model, embedding_size):
    print(len(word2id))
    word_vector = []
    unkown_vector = [i / (embedding_size + 0.0) for i in range(embedding_size)]
    word_vector.append(unkown_vector)
    wv_model = gensim.models.Word2Vec.load(w2v_model)
    word2id_ordered = OrderedDict(sorted(word2id.items(), key=lambda x: x[1]))
    for word in word2id_ordered.keys():
        if word in wv_model:
            word_vector.append(wv_model[word])
        else:
            word_vector.append([random.random() for i in range(embedding_size)])
    return np.array(word_vector)

############################################ 获取多类别标签(标签，类别数量) ############################################
def getMultihotLabel(labels, cate_num):
    multi_hot_label = [0]*cate_num  # [0,0,...,0]共30个
    for index in labels.strip().split(','):
        multi_hot_label[int(index)] = 1
    return multi_hot_label


def convert30CateData():
    train = open('../train.csv', 'r', encoding='utf8')
    o = open('../textPreprocess/train_convert10cates.txt', 'w', encoding='utf8')
    senti_vocab = open('../textPreprocess/train_senti_vocab.txt', 'w', encoding='utf8')
    rawCate = ['动力', '价格', '内饰', '配置', '安全性', '外观', '操控', '油耗', '空间', '舒适性']
    rawCateDict = {}
    doc2text = {}
    doc2cates = {}

    senti_word_set = []
    train.readline()

    for i, cate in enumerate(rawCate):
        rawCateDict[cate] = i + 1
    for line in train.readlines():
        line = line.strip().split(',')
        docid = line[0]  # reserve
        text = line[1]  # reserve
        subject = line[2]
        sentiment = int(line[3])
        senti_word = line[4]  # to get senti_vocab
        newCate = str((rawCateDict[subject] - 1) * 3 + (sentiment + 1))  # reserve
        if (len(senti_word) > 0 and senti_word not in senti_word_set):
            senti_word_set.append(senti_word)
            senti_vocab.write(senti_word + '\n')
        if (docid not in doc2text):
            doc2text[docid] = text
        if (docid not in doc2cates):
            doc2cates[docid] = [newCate]
        else:
            doc2cates[docid].append(newCate)
    print(len(doc2text))
    print(len(doc2cates))

    for docid in doc2text.keys():
        o.write(docid + '\t' + doc2text[docid] + '\t' + ','.join(doc2cates[docid]) + '\n')
    train.close()
    o.close()
    senti_vocab.close()


def convert10CateData():
    train = open('../train.csv', 'r', encoding='utf8')
    o = open('../textPreprocess/train_convert10cates.txt', 'w', encoding='utf8')
    senti_vocab = open('../textPreprocess/train_senti_vocab.txt', 'w', encoding='utf8')
    rawCate = ['动力', '价格', '内饰', '配置', '安全性', '外观', '操控', '油耗', '空间', '舒适性']
    rawCateDict = {}
    doc2text = {}
    doc2cates = {}

    senti_word_set = []
    train.readline()

    for i, cate in enumerate(rawCate):
        rawCateDict[cate] = i + 1
    for line in train.readlines():
        line = line.strip().split(',')
        docid = line[0]  # reserve
        text = line[1]  # reserve
        subject = line[2]
        sentiment = int(line[3])
        senti_word = line[4]  # to get senti_vocab
        newCate = str(rawCateDict[subject] - 1)  # reserve
        if (len(senti_word) > 0 and senti_word not in senti_word_set):
            senti_word_set.append(senti_word)
            senti_vocab.write(senti_word + '\n')
        if (docid not in doc2text):
            doc2text[docid] = text
        if (docid not in doc2cates):
            doc2cates[docid] = [newCate]
        else:
            doc2cates[docid].append(newCate)
    print(len(doc2text))
    print(len(doc2cates))

    for docid in doc2text.keys():
        o.write(docid + '\t' + doc2text[docid] + '\t' + ','.join(doc2cates[docid]) + '\n')
    train.close()
    o.close()
    senti_vocab.close()


############################################ 对类别进行解码 30分类 #####################################################
def decode30Cate(cateNum):
    rawCate = ['动力', '价格', '内饰', '配置', '安全性', '外观', '操控', '油耗', '空间', '舒适性']
    id2cate = {}
    for i, cate in enumerate(rawCate):  # 从0开始标序号
        id2cate[i+1] = cate  # 1-10
    cate = id2cate[int(cateNum/3)+1]  # 转换成类别
    sentiment = cateNum % 3-1  # -1,0,+1
    return cate, sentiment


############################################ 对类别进行解码 10分类 #####################################################
def decode10Cate(cateNum):
    rawCate = ['动力', '价格', '内饰', '配置', '安全性', '外观', '操控', '油耗', '空间', '舒适性']
    id2cate = {}
    for i, cate in enumerate(rawCate):  # 从0开始标序号
        id2cate[i] = cate  # 0-9
    cate = id2cate[int(cateNum)]  # 转换成类别
    sentiment = cateNum % 3-1  # -1,0,+1
    return cate, 0


def encode10Cate(cateName):
    rawCate = ['动力', '价格', '内饰', '配置', '安全性', '外观', '操控', '油耗', '空间', '舒适性']
    cate2id = {}
    for i, cate in enumerate(rawCate):  # 从0开始标序号
        cate2id[cate] = i  # 0-9
    return cate2id[cateName]


def getOneHotLabel(index, cate_num):
    one_hot_label = [0.0] * cate_num  # [0,0,...,0]共30个
    one_hot_label[index] = 1.0
    return one_hot_label


if __name__ == '__main__':

    # convert10CateData()

    ############################################## 获取训练集词典 ######################################################
    trainCorpusPath = '../textPreprocess/train_convert10cates.txt'
    testCorpusPath = '../test_public.csv'
    dict_file = '../textPreprocess/dict.txt'
    stop_words_file = '../case/stopwords.txt'
    car_list_file = '../case/car.txt'
    trainSinglePath = '../textPreprocess/trainSpecialWord.txt'
    testSinglePath = '../textPreprocess/testSpecialWord.txt'
    intersectionPath = '../textPreprocess/trainTestIntersectionWord.txt'
    topN = 30000
    digit_list = '../case/5_digit.txt'
    fraction_list = '../case/6_fraction.txt'
    distance_list = '../case/7_distance.txt'
    money_list = '../case/8_money.txt'
    city_list = '../case/9_city.txt'
    getNotCoveredData(trainCorpusPath, testCorpusPath, trainSinglePath, testSinglePath, intersectionPath, 17272, dict_file,
                      stop_words_file, car_list_file, digit_list, fraction_list, distance_list, money_list, city_list)


    ############################################## 获取w2v模型 #########################################################
    # w2v_data_file = '../data/w2v_data.txt'
    # w2v_result_file = '../data/w2v_data_result.txt'
    # yuliao_file = '../data/w2v_yuliao.txt'
    # dict_file = '../textPreprocess/dict.txt'
    # w2v_model = '../model/w2vmodel/w2vModel_100.model'
    # embedding_size = 100
    # car_list_file = '../case/car.txt'
    # digit_list_file = '../case/5_digit.txt'
    # fraction_list_file = '../case/6_fraction.txt'
    # distance_list_file = '../case/7_distance.txt'
    # money_list_file = '../case/8_money.txt'
    # city_list_file = '../case/9_city.txt'
    # get_w2v_model(w2v_data_file, w2v_result_file, yuliao_file, dict_file, w2v_model, embedding_size, car_list_file,
    #               digit_list_file, fraction_list_file, distance_list_file, money_list_file, city_list_file)

    ############################################## 获取w2v权重 #########################################################
    word2id = {}
    wordListFile = open('../textPreprocess/trainTestIntersectionWord.txt', 'r', encoding='utf8')
    wordListFile.readline()
    sum=0
    for line in wordListFile.readlines():
        sum += 1
        line = line.strip().split(',')
        word2id[line[0]] = int(line[2])  # word+id
        lens=len(word2id)
        if lens!=sum:
            print("diff:", len(word2id))
    print("sum", sum)
    w2v_model = '../model/w2vmodel/wiki_400.model'
    embedding_size = 400
    res = get_word_vector(word2id, w2v_model, embedding_size)
    print(res.shape)
    print(res.shape[0])

    ############################################## 获取句子长度 ########################################################
    # car_list_file = '../case/car.txt'
    # digit_list_file = '../case/5_digit.txt'
    # fraction_list_file = '../case/6_fraction.txt'
    # distance_list_file = '../case/7_distance.txt'
    # money_list_file = '../case/8_money.txt'
    # city_list_file = '../case/9_city.txt'
    # car_list, digit_list, fraction_list, distance_list, \
    # money_list, city_list = getList(car_list_file, digit_list_file, fraction_list_file,
    #                                 distance_list_file, money_list_file, city_list_file)
    # train = open('../textPreprocess/lesstrain_convert10cates.txt', 'r', encoding='utf8')
    # train = open('../test_public.csv', 'r', encoding='utf8')
    # max=0
    # sumindex=0
    # for line in train.readlines():
    #     line = line.strip().split(',')
    #     curSequence = getSequenceId(line[1], word2id, car_list, digit_list, fraction_list, distance_list, money_list,
    #                                 city_list, shuffle=False, drop=False)
    #     if lens>max:
    #         max=lens
    #     sumindex += 1
    # print(max)



