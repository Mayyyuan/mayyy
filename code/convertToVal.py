import copy

train = open('../textPreprocess/train_convert10cates.txt', 'r', encoding='utf8')
o_val = open('../textPreprocess/val_convert10cates_500.txt', 'w', encoding='utf8')
o_valData = open('../val_500.csv', 'w', encoding='utf8')
o_train = open('../textPreprocess/lesstrain_convert10cates_500.txt', 'w', encoding='utf8')
id2text = {}
id2label = {}
doc2label = {}
allid = []
for line in train.readlines():
    line = line.strip().split('\t')
    id = line[0]
    allid.append(id)
    text=line[1]
    label = line[2].strip().split(',')
    id2text[id] = text
    doc2label[id] = label
    for i in range(len(label)):
        if i == 0:
            id2label[id] = []
        id2label[id].append(int(label[i]))

all=0
count = [0 for i in range(11)]
for id in allid:
    if(len(id2label[id])) == 1:
        count[id2label[id][0]] += 1
        all += 1
    else:
        count[10] += 1
        all += 1

curcount = copy.deepcopy(count)
print(curcount)
print(count)
vallen=0
trainlen=0
o_valData.write("content_id,content\n")
for id in allid:
    if (len(id2label[id])) == 1:
        if curcount[id2label[id][0]]>count[id2label[id][0]] * 0.94:
            o_val.write(id + '\t' + id2text[id] + '\t' + ','.join(doc2label[id]) + '\n')
            o_valData.write(id + ',' + id2text[id] + '\n')
            vallen+=1
            curcount[id2label[id][0]] -= 1
        else:
            o_train.write(id + '\t' + id2text[id] + '\t' + ','.join(doc2label[id]) + '\n')
            trainlen += 1
            curcount[id2label[id][0]] -= 1
    else:
        if curcount[10] > count[10] * 0.94:
            o_val.write(id + '\t' + id2text[id] + '\t' + ','.join(doc2label[id]) + '\n')
            o_valData.write(id + ',' + id2text[id] + '\n')
            vallen += 1
            curcount[10] -= 1
        else:
            o_train.write(id + '\t' + id2text[id] + '\t' + ','.join(doc2label[id]) + '\n')
            trainlen+=1
            curcount[10] -= 1

o_val.close()
o_train.close()
o_valData.close()

print(curcount)
print(count)

print(vallen)
print(trainlen)


