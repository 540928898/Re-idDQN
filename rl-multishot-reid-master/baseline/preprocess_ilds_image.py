import os
import subprocess
import csv
import random
import glob
import numpy as np
'''
ROOT = '/data3/matt/iLIDS-VID'
output = '/data3/matt/iLIDS-VID/recs'
im2rec = '/home/zhangjianfu/reid/mxnet/bin/im2rec'
'''

ROOT = '/opt/iLIDS-VID'
output = '/opt/iLIDS-VID/recs'
im2rec = '/reid/mxnet/bin/im2rec'

sets = 0

def load_split():
    train, test, pool = [], [], []
    images, cnt = glob.glob('%s/i-LIDS-VID/images/cam1/person*/*.png' % (ROOT)), 0
    for i in images:
        t = int(i.split('/')[-2][-3:])
        cnt += 1
        pool.append(t)
    train = random.sample(pool, 150)
    for i in pool:
        if i not in train:
            test.append(i)
    print train, test
    print len(train), len(test)
    return train, test

def rnd_pos(N, i):
    x = random.randint(0, N - 2)
    return x + 1 if x == i else x

def save_rec(lst, path, name):
    lst_file = '%s/%s.lst' % (path, name)
    rec_file = '%s/%s.rec' % (path, name)
    #print lst_file, rec_file, '%s %s %s %s resize=128 quality=90' % (im2rec, lst_file, ROOT, rec_file)
    f = open(lst_file, "w")
    fo = csv.writer(f, delimiter='\t', lineterminator='\n')
    for item in lst:
        fo.writerow(item)
    f.close()
    f = open(rec_file, "w")
    fo = csv.writer(f, delimiter='\t', lineterminator='\n')
    for item in lst:
        fo.writerow(item)
    f.close()
    os.system('%s %s %s %s resize=128 quality=90' % (im2rec, lst_file, ROOT, rec_file))

def save_train(f, is_valid=False):
    plst, nlst, cnt, N, pool = [], [], 0, len(f[0]), [_ for _ in xrange(len(f[0]))]
    for _ in xrange(200 if not is_valid else 50):
        ts = random.sample(pool, 96)
        ns, ps = ts[:64], ts[64:]
        for r in xrange(32):
            i, x, y = ps[r], ns[r + r], ns[r + r + 1]
            p1 = (cnt, i, f[0][i][random.randint(0, len(f[0][i]) - 1)])
            p2 = (cnt + 1, i, f[1][i][random.randint(0, len(f[1][i]) - 1)])
            n1 = (cnt, x, f[1][x][random.randint(0, len(f[1][x]) - 1)])
            n2 = (cnt + 1, y, f[0][y][random.randint(0, len(f[0][y]) - 1)])
            cnt += 2
            plst.append(p1)
            plst.append(p2)
            nlst.append(n1)
            nlst.append(n2)
    save_rec(plst, output, 'image_' + ('valid' if is_valid else 'train') + '_even'+ str(sets))
    save_rec(nlst, output, 'image_' + ('valid' if is_valid else 'train') + '_rand'+ str(sets))

def save_test(f):
    lst, cnt_lst, cnt = [], [], 0
    '''for i in xrange(len(f[0])):
        lst.append((i * 2, 0, f[0][i][0]))
        lst.append((i * 2 + 1, 0, f[1][i][0]))'''
    for i in xrange(len(f[0])):
        cnt_lst.append(cnt)
        for j in f[0][i]:
            lst.append((cnt, 0, j))
            cnt += 1
    for i in xrange(len(f[1])):
        cnt_lst.append(cnt)
        for j in f[1][i]:
            lst.append((cnt, 1, j))
            cnt += 1
    cnt_lst.append(cnt)
    np.savetxt(output + '/image_test' + str(sets) + '.txt', np.array(cnt_lst), fmt='%d')
    save_rec(lst, output, 'image_test'+ str(sets))

def save_valid(f):
    lst, cnt_lst, cnt = [], [], 0
    '''for i in xrange(len(f[0])):
        lst.append((i * 2, 0, f[0][i][0]))
        lst.append((i * 2 + 1, 0, f[1][i][0]))'''
    for i in xrange(len(f[0])):
        cnt_lst.append(cnt)
        for j in f[0][i]:
            lst.append((cnt, 0, j))
            cnt += 1
    for i in xrange(len(f[1])):
        cnt_lst.append(cnt)
        for j in f[1][i]:
            lst.append((cnt, 1, j))
            cnt += 1
    cnt_lst.append(cnt)
    np.savetxt(output + '/image_valid' + str(sets) + '.txt', np.array(cnt_lst), fmt='%d')
    save_rec(lst, output, 'image_valid'+ str(sets))


def gen(train_lst, test_lst, ifshuffle):
    if ifshuffle:
        random.shuffle(train_lst)
        random.shuffle(test_lst)
    train, valid, test = [[], []], [[], []], [[], []]
    for i in xrange(3):
        lst = train_lst if i <= 1 else test_lst
        pool = train if i == 0 else (valid if i == 1 else test)
        for k in lst:
            for j in xrange(2):
                sets = 'images' if i == 1 else 'sequences'
                images = glob.glob('%s/i-LIDS-VID/%s/cam%d/person%03d/*.png' % (ROOT, sets, j + 1, k))
                #print k, j, images
                assert len(images) >= 1
#                g = [_[len(ROOT):] for  _ in images]
                
                #full path
                g = [_[:] for  _ in images]
                pool[j].append(g) # fix prefix

    save_train(train)
    save_train(valid, is_valid=True)
    save_test(test)
    save_valid(train)

if __name__ == '__main__':
    for i in xrange(10):
        print 'sets', sets
        train, test = load_split()
        gen(train, test, ifshuffle=True)
        sets += 1

