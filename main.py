from mpi4py import MPI
import sys
'''
    Uruchomienie programu następuje przy użyciu:
    mpiexec -n [liczba_procesów] python main.py [liczba gnomów] [liczba skrzatów]
    
    Przykład:
    mpiexec -n 5 python main.py 3 2
'''

# Ustawienia MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def get_messages():
    messages = []
    for i in range(size):
        status = MPI.Status()
        if comm.iprobe(source=i, status=status):
            message = comm.recv(source=i)
            messages.append((status.Get_source(), message))
    return messages


# Definicja typu procesu
G = int(sys.argv[1])
S = int(sys.argv[2])
if G + S != size:
    if rank == 0:
        exit("Liczba Skrzatów i Gnomów jest niezgodna")
    else:
        exit(-1)
if rank < G:
    process_type = "SKRZAT"
else:
    process_type = "GNOM"

# Lokalne struktury i zmienne
wait_queue = []
ack_counter = 0
ac = 5
b = 1
current_state = "REST"

if process_type == "GNOM":
    while True:
        if current_state == "REST":
            messages = get_messages()
            for message in messages:
                message_author = message[0]
                message_type = message[1]

                if message_type == "sREQ":
                    continue

                elif message_type == "qREQ":
                    comm.send("ACK", dest=message_author)

                elif message_type == "ACK":
                    continue

                elif message_type == "gCHG":
                    ac -= 1

                elif message_type == "sCHG":
                    ac += 1

            # Przejście do stanu INSECTION
            if ac >= G:
                current_state = "INSECTION"
            else:
                # Przejście do stanu WAIT
                ack_counter = 0
                comm.bcast("gREQ", root=rank) # Wysyłka do każdego procesu
                current_state = "WAIT"

        if current_state == "WAIT":
            messages = get_messages()
            for message in messages:
                message_author = message[0]
                message_type = message[1]

                if message_type == "sREQ":
                    continue

                elif message_type == "qREQ":
                    # TO DO - dodaj zegar Lamporta

                elif message_type == "ACK":
                    ack_counter += 1

                elif message_type == "gCHG":
                    ac -= 1

                elif message_type == "sCHG":
                    ac += 1
            
            # Przejście do stanu INSECTION
            if ack_counter >= G - ac:
                 current_state = "INSECTION"

        if current_state == "INSECTION":
            ac -= 1
            comm.bcast("gCHG", root=rank)

            messages = get_messages() # Może być problem, że jak program przejdzie do linijni niżej i dostanie wiadomość to skucha, bo jej nie uwzględnij
            for message in messages:
                message_author = message[0]
                message_type = message[1]

                if message_type == "sREQ":
                    continue

                elif message_type == "qREQ":
                    wait_queue.append(message_author)

                elif message_type == "ACK":
                    continue

                elif message_type == "gCHG":
                    ac -= 1

                elif message_type == "sCHG":
                    ac += 1

            # Przejście do stanu REST
            for target_rank in wait_queue:
                comm.send("ACK", dest=target_rank)
            wait_queue = []
            current_state = "REST"


elif process_type == "SKRZAT":
    while True:
        if current_state == "REST":
            messages = get_messages()
            for message in messages:
                message_author = message[0]
                message_type = message[1]

                if message_type == "gREQ":
                    continue

                elif message_type == "sREQ":
                    comm.send("ACK", dest=message_author)

                elif message_type == "ACK":
                    continue

                elif message_type == "sCHG":
                    b -= 1

                elif message_type == "gCHG":
                    b += 1

            # Przejście do stanu INSECTION
            if b >= S:
                current_state = "INSECTION"
            else:
                # Przejście do stanu WAIT
                ack_counter = 0
                comm.bcast("sREQ", root=rank)
                current_state = "WAIT"

        if current_state == "WAIT":
            messages = get_messages()
            for message in messages:
                message_author = message[0]
                message_type = message[1]

                if message_type == "gREQ":
                    continue

                elif message_type == "sREQ":
                # TO DO

                elif message_type == "ACK":
                    ack_counter += 1

                elif message_type == "sCHG":
                    b -= 1

                elif message_type == "gCHG":
                    b += 1

            # Przejście do stanu INSECTION
            if ack_counter >= S - b:
                current_state = "INSECTION"

        if current_state == "INSECTION":
            b -= 1
            comm.bcast("sCHG", root=rank)

            messages = get_messages()
            for message in messages:
                message_author = message[0]
                message_type = message[1]

                if message_type == "gREQ":
                    continue

                elif message_type == "sREQ":
                    wait_queue.append(message_author)

                elif message_type == "ACK":
                    continue

                elif message_type == "sCHG":
                    b -= 1

                elif message_type == "gCHG":
                    b += 1

            # Przejście do stanu REST
            for target_rank in wait_queue:
                comm.send("ACK", dest=target_rank)
            wait_queue = []
            current_state = "REST"



