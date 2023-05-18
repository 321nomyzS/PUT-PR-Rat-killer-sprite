from mpi4py import MPI
import time

def color_print_skrzat(text, rank, lamport_clock):
    colors = [
        '\033[31m',
        '\033[32m',
        '\033[34m',
        '\033[0m',
        '\033[33m',
        '\033[36m',
        '\033[35m',
        '\033[37m',
        '\033[90m',
        '\033[92m',
        '\033[96m',
        '\033[91m',
        '\033[95m'
    ]
    print(f"{colors[rank % len(colors)]}[SKRZAT:{rank} | {lamport_clock}] {text}")


def get_messages(comm, rank, lamport):
    messages = []
    while True:
        status = MPI.Status()
        #sprawdź czy jest wiadomosc do odebrania od obojętnie kogo. Jak jest, to zapisz o niej informacje w 'status'
        if comm.iprobe(source=MPI.ANY_SOURCE, status=status): 
            message = comm.recv(source=status.Get_source())
            color_print_skrzat(f"Otrzymalem wiadomosc {message} od {status.Get_source()}", rank, lamport)
            messages.append((status.Get_source(), message))
        else:
            break
    return messages


def skrzat_code(comm, S, b):
    # Ustawianie zmiennych i struktur lokalnych
    wait_queue = []
    ack_counter = 0
    current_state = "REST"

    # Ustawienia MPI
    rank = comm.Get_rank()
    size = comm.Get_size()

    lamport_clock = 0

    while True:
        if current_state == "REST":
            color_print_skrzat(f"Jestem w stanie REST", rank, lamport_clock)
            messages = get_messages(comm, rank, lamport_clock)

            for message in messages:
                message_author = message[0]
                message_type = message[1].split()[0]

                if message_type == "gREQ":
                    continue

                elif message_type == "sREQ":
                    color_print_skrzat(f"Odsylam wiadomosc ACK do {message_author}", rank, lamport_clock)
                    comm.send("ACK", dest=message_author)

                elif message_type == "ACK":
                    continue

                elif message_type == "sCHG":
                    b -= 1
                    color_print_skrzat(f"Zmniejszam b, teraz jest {b}", rank, lamport_clock)

                elif message_type == "gCHG":
                    b += 1
                    color_print_skrzat(f"Zwiekszam b, teraz jest {b}", rank, lamport_clock)

            # Przejście do stanu INSECTION
            if b >= S:
                current_state = "INSECTION"
            else:
                # Przejście do stanu WAIT
                ack_counter = 0
                lamport_clock += 1
                color_print_skrzat(f"Wysylam wiadomosc sREQ do wszystkich procesow", rank, lamport_clock)
                for i in range(size):
                    if i != rank:
                        comm.send(f"sREQ {lamport_clock}", dest=i)
                # comm.bcast(f"sREQ {lamport_clock}", root=rank)
                current_state = "WAIT"

        if current_state == "WAIT":
            color_print_skrzat(f"Jestem w stanie WAIT", rank, lamport_clock)
            
            while ack_counter < S - b:
                messages = get_messages(comm, rank, lamport_clock)

                for message in messages:
                    message_author = message[0]
                    message_type = message[1].split()[0]

                    if message_type == "gREQ":
                        continue

                    elif message_type == "sREQ":
                        message_clock = int(message[1].split()[1])
                        if lamport_clock <= message_clock:
                            color_print_skrzat(f"Odsylam wiadomosc ACK do {message_author}", rank, lamport_clock)
                            lamport_clock = message_clock + 1
                            comm.send("ACK", dest=message_author)
                        else:
                            lamport_clock += 1
                            wait_queue.append(message_author)

                    elif message_type == "ACK":
                        ack_counter += 1

                    elif message_type == "sCHG":
                        b -= 1
                        color_print_skrzat(f"Zmniejszam b, teraz jest {b}", rank, lamport_clock)

                    elif message_type == "gCHG":
                        b += 1
                        color_print_skrzat(f"Zwiekszam b, teraz jest {b}", rank, lamport_clock)

                # Przejście do stanu INSECTION
                # if ack_counter >= S - b:
            current_state = "INSECTION"

        if current_state == "INSECTION":
            color_print_skrzat(f"Jestem w stanie INSECTION", rank, lamport_clock)
            b -= 1
            color_print_skrzat(f"Zmniejszam b, teraz jest {b} i wysylam wiadomosc sCHG do wszystkich procesow", rank, lamport_clock)
            for i in range(size):
                if i != rank:
                    comm.send(f"sCHG", dest=i)
            # comm.bcast("sCHG", root=rank)

            messages = get_messages(comm, rank, lamport_clock) 

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
                    color_print_skrzat(f"Zmniejszam b, teraz jest {b}", rank, lamport_clock)

                elif message_type == "gCHG":
                    b += 1
                    color_print_skrzat(f"Zwiekszam b, teraz jest {b}", rank, lamport_clock)

            # Przejście do stanu REST
            for target_rank in wait_queue:
                color_print_skrzat(f"Wysylam wiadomosc ACK do {target_rank} znajdujacego sie w poczekalni", rank, lamport_clock)
                comm.send("ACK", dest=target_rank)
            wait_queue = []
            current_state = "REST"
            time.sleep(1)