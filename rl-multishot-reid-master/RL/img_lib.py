import mxnet as mx
import numpy as np
import cv2
import random


class ImgLibrary(mx.io.DataIter):
    '''
    Load images from disk/memory
    '''
    def __init__(self, lst_name, batch_size, aug_params=dict(), shuffle=False, data_dir=''):
        super(ImgLibrary, self).__init__()
        self.batch_size = batch_size
        self.aug_params = aug_params.copy()
        self.shuffle = shuffle
        self.data_dir = data_dir

        self.data, self.labels = ImgLibrary.load_data(lst_name, data_dir)
        #print "load data over"
        self.data_num = self.labels.shape[0]
        self.label_num = 1 if len(self.labels.shape) == 1 else self.labels.shape[1]
        #print self.data_num, self.label_num
        self.reset()
    @staticmethod
    def load_data(lst_name, data_dir):
        img_lst = [x.strip().split('\t')
                   for x in file(lst_name).read().splitlines()]
#        im = cv2.imread(data_dir + img_lst[0][-1])
        im = cv2.imread(img_lst[0][-1])
        print data_dir + img_lst[0][-1]
        h, w = im.shape[:2]
        n, m = len(img_lst), len(img_lst[0]) - 2
        data = []#np.zeros((n, h, w, 3), dtype=np.uint8)
        labels = np.zeros((n, m), dtype=np.int32) if m > 1 else np.zeros((n, ), dtype=np.int32)
        for i in range(len(img_lst)):
            #im = cv2.imread(data_dir + img_lst[i][-1])

            #data[i] = im
            
            # not data_dir it will duplicate /opt/id..!!!
#            data.append(data_dir + img_lst[i][-1])
            data.append(img_lst[i][-1])
            labels[i] = img_lst[i][1:-1] if m > 1 else img_lst[i][1]

        data = np.array(data)

        return data, labels

    @staticmethod
    def even_shuffle(labels):
        '''
        shuffle images lists and make pairs
        '''
        s = [(x, int(random.random() * 1e5), i) for i, x in enumerate(labels)]
        s = sorted(s, key=lambda x: (x[0], x[1]))
        lst = [x[2] for x in s]

        idx = range(0, len(lst), 2)
        random.shuffle(idx)
        ret = []
        for i in idx:
            ret.append(lst[i])
            ret.append(lst[i + 1])

        return ret

    @staticmethod
    def model_shuffle(labels):
        '''
        shuffle images and images with same model are grouped together
        '''
        models_idx = range(int(np.max(labels)) + 1)
        random.shuffle(models_idx)
        s = [(models_idx[x], int(random.random() * 1e5), i) for i, x in enumerate(labels)]
        s = sorted(s, key=lambda x: (x[0], x[1]))
        lst = [x[2] for x in s]

        return lst

    def reset(self):
        self.current = 0
        if self.shuffle:
            #idx = ImgLibrary.even_shuffle(self.labels)
            idx = ImgLibrary.model_shuffle(self.labels)
            self.data = self.data[idx]
            self.labels = self.labels[idx]

    @property
    def provide_data(self):
        shape = self.aug_params['input_shape']

        return [('data', (self.batch_size, shape[0], shape[1], shape[2]))]

    @property
    def provide_label(self):
        return [('softmax_label', (self.batch_size, self.label_num))]

    @staticmethod
    def augment(im, aug_params, aug=False):
        '''
        augmentation (resize, crop, mirror)
        '''
        crop_h, crop_w = aug_params['input_shape'][1:]
        ori_h, ori_w = im.shape[:2]
        resize = aug_params['resize']
        if ori_h < ori_w:
            h, w = resize, int(float(resize) / ori_h * ori_w)
        else:
            h, w = int(float(resize) / ori_w * ori_h), resize

        if h != ori_h:
            im = cv2.resize(im, (w, h), interpolation=cv2.INTER_LINEAR)

        x, y = (w - crop_w) / 2, (h - crop_h) / 2
        if aug_params['rand_crop'] and aug:
            x = random.randint(0, w - crop_w)
            y = random.randint(0, h - crop_h)
        im = im[y:y + crop_h, x:x + crop_w, :]

        # cv2.imshow("name", im.astype(np.uint8))
        # cv2.waitKey()

        # Blur
        '''org = x.asnumpy()
        sig = random.random() * 5
        result = np.zeros_like(org)
        for i in xrange(3):
            result[0, i, :, :] = ndimage.gaussian_filter(org[0, i, :, :], sig)
        print sig
        import cv2
        cv2.imshow("name", (result[0].transpose(1, 2, 0)+128).astype(np.uint8))
        cv2.waitKey()
        cv2.imshow("name", (org[0].transpose(1, 2, 0)+128).astype(np.uint8))
        cv2.waitKey()'''

        im = np.transpose(im, (2, 0, 1))
        newim = np.zeros_like(im)
        newim[0] = im[2]
        newim[1] = im[1]
        newim[2] = im[0]

        if aug and aug_params['rand_mirror'] and random.randint(0, 1) == 1:
            newim = newim[:, :, ::-1]
        newim -= aug_params['mean']

        return newim

    def get_single(self, i, aug=False):
        im = cv2.imread(self.data[i]).astype(np.float32)
        im = ImgLibrary.augment(im, self.aug_params, aug)
        return im

    def next(self):
        #if self.current + self.batch_size > self.data_num:
        if self.current > self.data_num:
            raise StopIteration

        shape = self.aug_params['input_shape']
        x = np.zeros((self.batch_size, shape[0], shape[1], shape[2]))
        y = np.zeros((self.batch_size, self.label_num) if self.label_num > 1
                     else (self.batch_size, ))
        index = []
        for i in range(self.current, self.current + self.batch_size):
            im = cv2.imread(self.data[i % self.data_num]).astype(np.float32)
            im = ImgLibrary.augment(im, self.aug_params)
            x[i - self.current] = im
            y[i - self.current] = self.labels[i % self.data_num]
            index.append(i)

        #x -= self.aug_params['mean']

        x = mx.nd.array(x)
        label = mx.nd.array(y)

        batch = mx.io.DataBatch(data=[x], label=[label], pad=0, index=index)
        self.current += self.batch_size

        return batch