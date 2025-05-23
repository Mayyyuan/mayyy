def evaluate(val_predict_file, train_corpus):
    predict_file = open(val_predict_file, 'r', encoding='utf8')
    train_corpus = open(train_corpus, 'r', encoding='utf8')

    predict_file.readline()
    train_corpus.readline()
    predict_lines = predict_file.readlines()
    train_lines = train_corpus.readlines()
    Tp = 0
    train_total = 0
    test_total = 0

    contentid_predict = {}
    id_predict = 0
    for i in range(len(predict_lines)):
        test_total += 1
        id_predict_last = id_predict
        id_predict = predict_lines[i].strip().split(',')[0]
        sub_predict = predict_lines[i].strip().split(',')[1]
        # sen_predict = predict_lines[i].strip().split(',')[2]
        sen_predict = str(0)
        if id_predict_last == id_predict:
            contentid_predict[id_predict].append([sub_predict, sen_predict])
        else:
            contentid_predict[id_predict] = [[sub_predict, sen_predict]]

    for i in range(len(train_lines)):
        train_total += 1
        id_train = train_lines[i].strip().split(',')[0]
        sub_train = train_lines[i].strip().split(',')[2]
        # sen_train = train_lines[i].strip().split(',')[3]
        sen_train = str(0)
        result_train = [sub_train, sen_train]
        if result_train in contentid_predict[id_train]:
            Tp += 1
    predict_file.close()
    train_corpus.close()
    Fp = test_total - Tp
    Fn = train_total - Tp
    P = Tp / (Tp + Fp)
    R = Tp / (Tp + Fn)
    F1 = 2 * P * R / (P + R)
    return F1


if __name__ == "__main__":
    print("start...")
    predict_file = '../result/val_public_predict_0929.csv'
    train_corpus = '../valData.csv'


    F1 = evaluate(predict_file, train_corpus)
    print(F1)
