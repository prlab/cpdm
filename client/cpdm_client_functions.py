import numpy as np
import scipy.io as sio


def neighbours1(s=None, W=None):
    # input: the graph edges and a vertice 's'
    # output: neighbours of 's'

    return np.nonzero(W[s, :])[0]


# Voithitiki Sunartisi pou vriskei tous kontinous geitones



def density(nodes=None, W=None):
    v = len(nodes)
    den = 0

    if v < 2:
        # we check in DMSP and never call density with |nodes|<2

        den = 1000000000
        return den

        for i in range(0, (v - 1)):
            for j in range((i + 1), v):
                # if nodes not connected, w=0 [function weight instead of weight_all]!
                den = den + W[nodes[i], nodes[j]]

        den = 2 * den / (v * (v - 1))
    # !!! undirected graph: all possible edges v * (v-1) / 2 !!!
    return den


# H Vasiki mas Sunarthsh, edw ginontai oi diadikasies me tis opoies vriskoume ta upodiktyo
# Lamvanontas upopsin tis 2 metrikes

def DMSP_new(s, parameters):

    # Detect Module from Seed Protein

    # print "SEED PROTEIN NUMBER", s
    p = [parameters[0], parameters[1]]  # eq 2
    p2 = parameters[2] # eq4 , ideally -> 1.0
    level = parameters[3]

    file_w = sio.loadmat(parameters[4])
    W = file_w['w']
    #print W

    # Kernel - Arxikos upografos = Ks
    # Ks=all neighbours of s
    Ks = np.array(neighbours1(s, W))
    # if len(Ks) < 2:
    #	return Ks
    # print "GIA TO SEED PROTEIN : ",s

    starters = len(Ks)

    io = np.zeros(len(Ks))  # !!!!!!!!!!!
    dis = np.ones(len(Ks), dtype=bool)
    # io_w = io;
    discard = io
    '''
    if len(Ks) < 100:
        division = len(Ks) // 10 #ta Ks poy tha parei kathe VM
    '''

    # print "\n ARITHMOS ARXIKWN GEITONWN EINAI  " , len(Ks) , "  FOR SEED " , s

    # print "Arxikoi Geitones:  \n" ,division


    lists = []
    c = 0
    for i in range(0, len(Ks), 5):
        lists.append(Ks[i:i + 5])
        c = c + 1
    # print c





    for i in range(len(Ks)):
        nb = neighbours1(Ks[i], W)
        nb_int = np.intersect1d(nb, Ks)  # !!!!!! to do
        nb_ext = np.setdiff1d(nb, nb_int)  # !!! to do
        N_int = len(nb_int)  # Epistrefei arithmo stilwn to do

        N_ext = len(nb_ext);

        b_int = 0
        if N_int != 0:
            for j in range(N_int):
                b_int = b_int + W[Ks[i], nb_int[j]];
            b_int = b_int * 1.0 / N_int

        b_ext = 0
        if N_ext != 0:
            for j in range(0, N_ext):
                b_ext = b_ext * 1.0 + W[Ks[i], nb_ext[j]]
            b_ext = b_ext * 1.0 / N_ext
        # Analuoyme tous vathmous kai analoga vgazoume ta nodes apo to Kernel
        # check eq. 2
        # check weightened degrees
        if N_int == 0 & N_ext == 0:
            N_int = 1
        io[i] = N_int * 1.0 / (N_int + N_ext)

        # print N_int, N_ext, N_int * 1.0 / (N_int + N_ext);
        # print "io < p[0] -> ", io[i] , " < ", p[0], " = ", io[i] < p[0];
        if io[i] < p[0] or b_int > b_ext:
            # mark to discard
            dis[i] = False;
            discard[i] = 1  # to-check
        else:
            discard[i] = 0
            dis[i] = True

    dislist = []
    c = 0
    for i in range(0, len(dis), 5):
        dislist.append(dis[i:i + 5])
        c = c + 1

    # Ks(discard > 0).lvalue = mcat([]) # to-do
    # io(discard > 0).lvalue = mcat([])





    # for i in range(0,len(Ks),5):
    Ks = Ks[dis]

    iox = np.array(io);
    iox = iox[dis];

    _Ks = [];
    _io = []
    for x in range(len(Ks)):
        _Ks.append(Ks[x])
        _io.append(iox[x]);

    Ks = _Ks
    io = _io;

    sum1 = zip(io, Ks)
    sum1.sort()

    for i in range(len(sum1)):
        sum1[i] = sum1[i][1]

    Ks = sum1
    # print "Ks sorted: ", Ks;
    # add s to module !!
    Ks = Ks + [s]

    # check eq. 3: find min density,
    # by removing one node each time starting from most insignificant
    # Vgazoume enan enan tous ligotero shmantikous nodes kai kathe fora metrame #thn puknotita
    dmin = density(Ks, W)
    delsize = 1
    # display(['Before step 3: ' num2str(size(Ks,1))])
    for i in range(1, len(Ks) - 1):
        d = density(Ks[i:], W)
        if d < dmin:
            dmin = d
            delsize = i
    # display(['Before step 3: ' num2str(delsize)])


    Ks = Ks[delsize - 1:]

    # ftiaxnoume ton teliko ypografo
    # iteration by adding neighbors [2nd, 3rd level...]
    for lvl in range(2, level + 1):
        Ntemp = len(Ks)  # to-do

        for i in range(0, Ntemp):
            next_nb = neighbours1(Ks[i], W)
            #print next_nb
            #print Ks
            next_nb = np.setdiff1d(next_nb, Ks)  # remove already included neighbours
            next_nb = np.setdiff1d(next_nb, s)  # remove seed

            for j in range(0, len(next_nb)):
                # check eq 2
				
                nb_temp = neighbours1(next_nb[j], W)
                nb_int = np.intersect1d(nb_temp, Ks)
                nb_ext = np.setdiff1d(nb_temp, nb_int)
                N_int = len(nb_int)
                N_ext = len(nb_ext)
                err = N_int + N_ext
                if err == 0:
                    err = 1
                io = N_int * 1.0 / err

                if io < p[1]:
                    # discard
                    continue

                # calculate b_int
                b_int = 0
                if N_int != 0:
                    for k in range(0, N_int):
                        b_int = b_int + W[next_nb[j], nb_int[k]]
                    b_int = b_int * 1.0 / N_int

                # check eq 4
                # if W(Ks(i),next_nb(j)) <= p2 * b_int
                # add node
                #       Ks=[Ks, next_nb(j)];
                # end

                b_ext = 1
                if N_ext != 0:
                    b_ext = 0
                    for k in range(0, N_ext):
                        b_ext = b_ext + W[next_nb[j], nb_ext[k]]
                    b_ext = b_ext * 1.0 / N_ext

                if b_int <= p2 * b_ext:
                    Ks = Ks + [next_nb[j]]
    # print "FOR SEED PROTEIN : ", s
    # print "		FINAL SUGRAPH IS: \n" ,Ks
    return (Ks, s, starters)

# epistrefontai ta apairaitita stoixeia tou upodiktuoy
if __name__=='__main__':
	print DMSP_new(26, [0.45, 0.75, 0.9, 2, '/export/02e37d66-5782-11e7-bda7-02005f6f040d/w.mat'])