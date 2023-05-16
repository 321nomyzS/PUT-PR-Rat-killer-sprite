from mpi4py import MPI
import sys
'''
    Uruchomienie programu następuje przy użyciu:
    mpiexec -n [liczba_procesów] python main.py [liczba gnomów] [liczba skrzatów]
    
    Przykład:
    mpiexec -n 5 python main.py 3 2
'''

# Ustawanie początkowych wartości ac oraz b
ac = 5
b = 1


if __name__ == "__main__":
    # Definicja struktury MPI
    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()

    # Definicja typu procesu
    G = int(sys.argv[1])
    S = int(sys.argv[2])
    if G + S != size:
        if rank == 0:
            exit("Liczba Skrzatów i Gnomów jest niezgodna")
        else:
            exit(-1)

    if rank < S:
        # Program dla skrzata
        from skrzat import skrzat_code
        skrzat_code(comm=comm, S=S, b=b)
    else:
        # Program dla gnoma
        from gnom import gnome_code
        gnome_code(comm=comm, G=G, ac=ac)



