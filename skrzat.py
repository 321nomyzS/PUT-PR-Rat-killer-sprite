from mpi4py import MPI

def get_messages(comm, size):
    messages = []
    for i in range(size):
        status = MPI.Status()
        if comm.iprobe(source=i, status=status):
            message = comm.recv(source=i)
            messages.append((status.Get_source(), message))
    return messages

def skrzat_code(comm, S, b):
    # Ustawianie zmiennych i struktur lokalnych
    wait_queue = []
    ack_counter = 0
    current_state = "REST"

    # Ustawienia MPI
    rank = comm.Get_rank()
    size = comm.Get_size()

    while True:
        if current_state == "REST":
            messages = get_messages(comm, size)
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
            messages = get_messages(comm, size)
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

            messages = get_messages(comm, size)
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