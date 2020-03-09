import numpy as np
import math
import logging
from model import model

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logfile_handler = logging.FileHandler('mcmc.log')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logfile_handler.setFormatter(formatter)
logger.addHandler(logfile_handler)

mcmc_model = model()


def read_no_of_sites_taxa(file):
    str = file.readline()
    N, M = map(int, str.split())
    return N, M


def construct_matrix(file):

    N = mcmc_model.N
    M = mcmc_model.M

    data_matrix_shape = (N, M)
    X = np.zeros(data_matrix_shape)
    hard_sites_vector_shape = (N, 1)
    H = np.zeros(hard_sites_vector_shape)
    Nh = 0
    for i in range(N):
        str = file.readline()
        for j in range(M):
            X[i][j] = str.split(" ")[j]
        try:
            if(str.split(" ")[M] == '*'):
                H[i][0] = 1
                Nh = Nh + 1
        except IndexError:
            pass
    return X, H, Nh


def compute_lifespan():

    N = mcmc_model.N
    M = mcmc_model.M
    X = mcmc_model.X
    rpi = mcmc_model.rpi

    lifespan_matrix_shape = (M, 1)
    a = np.zeros(lifespan_matrix_shape)
    b = np.zeros(lifespan_matrix_shape)

    """
    Zero-indexing in lifespan matrices. Reference code uses one-indexing for death site vector
    """

    for m in range(M):
        n = 0
        while (n < N and not X[rpi[n]][m]):
            n += 1
        if (n is N):
            print("Zero column at", m, ", continuing.")
            a[m] = 0
            b[m] = N
        else:
            a[m] = n
            n = N-1
            while(n >= (a[m]-1) and not X[rpi[n]][m]):
                n -= 1
            b[m] = n+1
    return a, b


def init_log_prob():

    M = mcmc_model.M

    log_prob_matrix_shape = (M, 1)
    c = np.zeros(log_prob_matrix_shape)
    d = np.zeros(log_prob_matrix_shape)
    for m in range(M):
        c[m] = math.log(0.01, math.e)
        d[m] = math.log(0.3, math.e)
    return c, d


def compute_trfa_count():

    N = mcmc_model.N
    M = mcmc_model.M
    X = mcmc_model.X
    pi = mcmc_model.pi
    rpi = mcmc_model.rpi
    a = mcmc_model.a
    b = mcmc_model.b

    n, m = [0]*2
    tr0a, tr1a, fa0a, fa1a = [0]*4
    count_matrix_shape = (M, 1)
    tr0 = np.zeros(count_matrix_shape)
    tr1 = np.zeros(count_matrix_shape)
    fa0 = np.zeros(count_matrix_shape)
    fa1 = np.zeros(count_matrix_shape)
    for m in range(M):
        t0, f0, t1, f1 = [0]*4
        for n in range(N):
            if (a[m] <= pi[n] and pi[n] < b[m]):
                if (X[n][m]):
                    t1 += 1
                else:
                    f0 += 1
            else:
                if (X[n][m]):
                    f1 += 1
                else:
                    t0 += 1

        tr0a += t0
        tr1a += t1
        fa0a += f0
        fa1a += f1

        tr0[m] = t0
        tr1[m] = t1
        fa0[m] = f0
        fa1[m] = f1

    return tr0, tr1, fa0, fa1, tr0a, tr1a, fa0a, fa1a


def compute_loglike():

    M = mcmc_model.M
    c = mcmc_model.c
    d = mcmc_model.d
    tr0 = mcmc_model.tr0
    tr1 = mcmc_model.tr1
    fa0 = mcmc_model.fa0
    fa1 = mcmc_model.fa1

    loglike = 0
    for m in range(M):
        cur_c = c[m]
        cur_d = d[m]
        temp_sum = tr0.item(m)*math.log(1-math.exp(cur_c),
                                        math.e) + fa0.item(m)*(cur_d) + fa1.item(m)*(cur_c) + tr1.item(m)*math.log(1-math.exp(cur_d), math.e)
        loglike += temp_sum
    return loglike


def read_model(file):
    N, M = read_no_of_sites_taxa(file)
    mcmc_model.N = N
    mcmc_model.M = M

    X, H, Nh = construct_matrix(file)
    mcmc_model.X = X
    mcmc_model.H = H
    mcmc_model.Nh = Nh

    mcmc_model.pi = np.arange(0, mcmc_model.N, 1)
    mcmc_model.rpi = np.argsort(mcmc_model.pi)

    a, b = compute_lifespan()
    mcmc_model.a = a
    mcmc_model.b = b

    logger.debug(a)

    c, d = init_log_prob()
    mcmc_model.c = c
    mcmc_model.d = d

    tr0, tr1, fa0, fa1, tr0a, tr1a, fa0a, fa1a = compute_trfa_count()
    mcmc_model.tr0 = tr0
    mcmc_model.tr1 = tr1
    mcmc_model.fa0 = fa0
    mcmc_model.fa1 = fa1
    mcmc_model.tr0a = tr0a
    mcmc_model.tr1a = tr1a
    mcmc_model.fa0a = fa0a
    mcmc_model.fa1a = fa1a

    mcmc_model.loglike = compute_loglike()

    return mcmc_model
