import random
import numpy as np
from numpy.linalg import norm as npnorm
from keras.models import Sequential, model_from_json
from keras.layers.core import Dense, Dropout, Activation


'''
Implementation of the networks trained from the dataset.  The networks are used
to approximate 3 functions: the value function V(a,b) which is the minimal cost
to pay for going from a to b ; the X- ; and the U-trajectories X(a,b) and
U(a,b) which are the state and control trajectories to go from a to b.
'''

TRAJLENGTH = 21


class Networks:
    BATCH_SIZE = 128

    def __init__(self, state_size, control_size):
        self.TRAJLENGTH = TRAJLENGTH
        self.state_size = state_size
        self.control_size = control_size

        self.value = self._create_model(state_size * 2, 1)
        self.ptrajx = self._create_model(state_size * 2,
                                         state_size * self.TRAJLENGTH)
        self.ptraju = self._create_model(state_size * 2,
                                         control_size * self.TRAJLENGTH)

    def train(self, dataset, nepisodes=int(1e2)):
        # TODO track
        # TODO normalization
        for episode in range(nepisodes):
            batch = random.choices(
                range(len(dataset.us)), k=self.BATCH_SIZE*16)
            xbatch = np.hstack([dataset.x1s[batch, :], dataset.x2s[batch, :]])

            self.value.fit(xbatch, dataset.vs[batch, :],
                           batch_size=self.BATCH_SIZE,
                           epochs=1, verbose=True)
            self.ptrajx.fit(xbatch, dataset.trajxs[batch, :],
                            batch_size=self.BATCH_SIZE,
                            epochs=1, verbose=False)
            self.ptraju.fit(xbatch, dataset.trajus[batch, :],
                            batch_size=self.BATCH_SIZE,
                            epochs=1, verbose=False)

    def trajectories(self, x1=None, x2=None):
        """
        Returns a triplet X,U,V (ie a vector sampling the time function) to go
        from x0 to x1, computed from the networks (global variable).
        """
        x = np.hstack([x1, x2]).reshape((1, 2*self.state_size))

        X = self.ptrajx.predict(x, batch_size=self.BATCH_SIZE)
        X = X.reshape((self.TRAJLENGTH, self.state_size))
        U = self.ptraju.predict(x, batch_size=self.BATCH_SIZE)
        U = U.reshape((self.TRAJLENGTH, self.control_size))
        V = self.value.predict(x, batch_size=self.BATCH_SIZE)
        return X, U, V

    def _create_model(self, input_size, output_size, nb_layer1=250,
                      nb_layer2=250):
        model = Sequential()
        model.add(Dense(nb_layer1, kernel_initializer='lecun_uniform',
                        input_shape=(input_size,)))
        model.add(Activation('relu'))
        model.add(Dropout(0.2))
        model.add(Dense(nb_layer2, kernel_initializer='lecun_uniform'))
        model.add(Activation('relu'))
        model.add(Dropout(0.2))
        model.add(Dense(output_size, kernel_initializer='lecun_uniform'))
        model.add(Activation('linear'))
        model.compile(loss='mse', optimizer="rmsprop")
        return model

    def connect_test(self, x1, x2):
        x = np.hstack([x1, x2]).reshape((1, 2*self.state_size))
        return self.ptrajx.predict(x, batch_size=self.BATCH_SIZE)

    def connect(self, x1, x2):
        pass


class Dataset:
    def __init__(self, graph):
        self.graph = graph
        self.indexes = []
        self.set()

    def __str__(self):
        return '\n'.join([
            '##################',
            'Dataset:',
            'Number of X traj: ' + str(len(self.trajxs)),
            'Number of U traj: ' + str(len(self.trajus)),
        ])

    def set(self):
        x1s = []  # init points
        x2s = []  # term points
        vs = []  # values
        us = []  # controls
        trajxs = []  # trajs state
        trajus = []  # trajs state

        # TODO: LENT!
        print('Load dataset ')
        # for every edge trajectory
        for (p1, p2), (X, U, V) in self.graph.edges.items():
            print('.', end='')
            DV = V / (len(X) - 1)
            # for every instant of the trajectory
            for k, (x1, u1) in enumerate(zip(X, U)):
                # Create subtrajectory of minimum size 7 to the end of the traj
                # resample this trajectory: if trajectory length < 21: more
                # points, otherwise less
                for di, x2 in enumerate(X[k+1:]):
                    if di < 5:
                        continue
                    x1s.append(x1)
                    x2s.append(x2)
                    us.append(u1)
                    vs.append(DV * (di + 1))
                    # np.ravel -> flatten any array in a 1D array

                    trajxs.append(np.ravel(resample(X[k:k+di+2], TRAJLENGTH)))
                    trajus.append(np.ravel(resample(U[k:k+di+2], TRAJLENGTH)))
                    self.indexes.append([p1, p2, k, di])

        print('\n')
        self.x1s = np.vstack(x1s)
        self.x2s = np.vstack(x2s)
        self.vs = np.vstack(vs)
        self.us = np.vstack(us)
        self.trajxs = np.vstack(trajxs)
        self.trajus = np.vstack(trajus)


def resample(X, N):
    """
    Resample in N iterations the trajectory X. The output is a
    trajectory similar to X with N points. Whatever the length of X (longer
    or shorter than N), the trajectories out are all of size N.
    """
    # TODO: Maybe better than a loop?
    # Number of points in the trajectory X
    nx = X.shape[0]
    idx = (np.arange(float(N)) / (N - 1)) * (nx - 1)
    hx = []
    for i in idx:
        i0 = int(np.floor(i))
        i1 = int(np.ceil(i))
        di = i % 1
        # barycenter of the to closest points in X
        x = X[i0, :] * (1 - di) + X[i1, :] * di
        hx.append(x)

    # could use np.array but sometimes better performances with vstack
    return np.vstack(hx)
