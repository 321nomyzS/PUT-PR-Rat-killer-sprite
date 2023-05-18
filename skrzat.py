from mpi4py import MPI
import colorama
from colorama import Fore

def get_messages(comm, rank, size):
    messages = []
    for i in range(size):
        status = MPI.Status()
        if comm.iprobe(source=i, status=status):
            message = comm.recv(source=i)
            print(f"[SKRZAT:{rank}] Otrzymałem wiadomość {message} od {i}")
            messages.append((status.Get_source(), message))
    return messages

def skrzat_code(comm, S, b):
    # Ustawianie zmiennych i struktur lokalnych
    wait_queue = []
    ack_counter = 0
    current_state = "REST"
    lamport_clock = 0

    # Ustawienia MPI
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Ustawianie koloru tekstów
    colorama.init()
    available_colors = [Fore.RED, Fore.GREEN, Fore.BLUE, Fore.YELLOW, Fore.MAGENTA, Fore.CYAN]
    print(available_colors[rank % len(available_colors)], end='')

    while True:
        if current_state == "REST":
            print(f"[SKRZAT:{rank}] Jestem w stanie REST")
            messages = get_messages(comm, rank, size) # TO DO: Wiadomości powinny być odbierane w pętli do jakiegoś momentu.
            # Możliwe, że wiadomość dojdzie do procesu w momencie, jak proces będzie linijkę niżej. Wtedy wiadomość nie zostanie uwzględniona

            for message in messages:
                message_author = message[0]
                message_type = message[1].split()[0]

                if message_type == "gREQ":
                    continue

                elif message_type == "sREQ":
                    comm.send("ACK", dest=message_author)
                    print(f"[SKRZAT:{rank}] Odsyłam wiadomość ACK do {message_author}")

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
                lamport_clock += 1
                comm.bcast(f"sREQ {lamport_clock}", root=rank)
                current_state = "WAIT"

        if current_state == "WAIT":
            print(f"[SKRZAT:{rank}] Jestem w stanie WAIT")
            messages = get_messages(comm, rank, size) # TO DO: Wiadomości powinny być odbierane w pętli do jakiegoś momentu.
            # Możliwe, że wiadomość dojdzie do procesu w momencie, jak proces będzie linijkę niżej. Wtedy wiadomość nie zostanie uwzględniona

            for message in messages:
                message_author = message[0]
                message_type = message[1].split()[0]

                if message_type == "gREQ":
                    continue

                elif message_type == "sREQ":
                    message_clock = int(message[1].split()[1])
                    if lamport_clock < message_clock:
                        lamport_clock = message_clock + 1
                        comm.send("ACK", dest=message_author)
                    else:   
                        lamport_clock += 1 
                        wait_queue.append(message_author)

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
            print(f"[SKRZAT:{rank}] Jestem w stanie INSECTION")
            b -= 1
            comm.bcast("sCHG", root=rank)
            print(f"[SKRZAT:{rank}] Wysyłam wiadomość sCHG do wszystkich procesów")

            messages = get_messages(comm, rank, size) # TO DO: Wiadomości powinny być odbierane w pętli do jakiegoś momentu.
            # Możliwe, że wiadomość dojdzie do procesu w momencie, jak proces będzie linijkę niżej. Wtedy wiadomość nie zostanie uwzględniona

            for message in messages:
                message_author = message[0]
                message_type = message[1].split()[0]

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
                print(f"[SKRZAT:{rank}] Wysyłam wiadomość ACK do {target_rank}")
            wait_queue = []
            current_state = "REST"