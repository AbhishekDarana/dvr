import sys
import threading
from _thread import *
import socket
import ast

topology=[]
threads=[]

socket_list=[]
name_list=[]
round=1
count = 0
full_update=0

final_dv={}
last_dv={}
thread_list=[]
neighbour_dict={}

def network_init(name,host,matrix):  # Node thread function has relatuve Distance Vector(DV)
    
    global topology
    global name_list
    
    neighbour_dict={}
    length_of_top=len(matrix)
    dv_matrix={}
    
    
    
    for i in range(length_of_top):
        if i==name:
            dv_matrix[chr(65+i)]=0
        elif matrix[i] !=0:
            dv_matrix[chr(65+i)]=matrix[i]
            neighbour_dict[chr(65+i)]=matrix[i]
        else:
            dv_matrix[chr(65+i)]=999

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind the socket to a public host, and a well-known port
    
    s.bind(host)
    # Making it a server socket
    s.listen(5)
    
    while True:
        try:
            
            client_socket, addr = s.accept()
            data = client_socket.recv(1024).decode()
            
            node_name,ext_data=data.split("*")
            if ext_data=="BYE":
                client_socket.shutdown(socket.SHUT_RDWR)
                client_socket.close()
                break

            
            sent_dv=ast.literal_eval(ext_data)
            
            
            if node_name!=chr(65+name):
                if node_name in name_list:
                    ind=name_list.index(node_name)
                via_dist=dv_matrix[name_list[ind]]
                for i in sent_dv:
                    if sent_dv[i]==999:
                        continue
                    dv_matrix[i]=min(via_dist+sent_dv[i],dv_matrix[i])
                
                    
                print("Node {0} received DV from node {1}".format(chr(65+name), name_list[ind]))
                print("Updating DV matrix at node {0}".format(chr(65+name)))
                
                
                print("New DV matrix at node {0}: {1}\n".format(chr(65+name),dv_matrix))
                
            client_socket.send((str(dv_matrix)).encode())
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
            
        except socket.error as ex:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
            

if __name__ == "__main__":
    dv={}
    last_dv={}
    if len(sys.argv)>1:                     # Check if an input file is given
        input_file=sys.argv[1]
        
        file1 = open(input_file, 'r')
        
        for line in file1:
            count+=1
            str1=line.strip()
            topology.append(ast.literal_eval(str1)) # Adds all the rows in the file to the topology
        file1.close()
        
        length_of=len(topology)
        for i in range(0,length_of):
            neighbour_dict[chr(65+i)]={}
            for j in range(0,length_of):
                if topology[i][j]!=0:
                    neighbour_dict[chr(65+i)][chr(65+j)]=topology[i][j]
            host=(socket.gethostname(), 12400+i)
            socket_list.append(host)                # Add all sockets to a list-----socket_list
            name_list.append(chr(65+i))             # Add all Node names to the list---name_list
            final_dv[chr(65+i)]=topology[i]
            t=threading.Thread(target=network_init, args=(i,host,topology[i]))   # Create n nodes  for n rows of the file
            threads.append(t)
        
        for i in threads:
            i.start()
        
        initial_supp={}
        
        for i in range(0,length_of):
            initial_supp[chr(65+i)]={}
            for j in range(0,length_of):
                if j==i:
                    initial_supp[chr(65+i)][chr(65+j)]=0
                else:
                    if final_dv[chr(65+i)][j]==0:
                        initial_supp[chr(65+i)][chr(65+j)]=999
                    else:
                        initial_supp[chr(65+i)][chr(65+j)]=final_dv[chr(65+i)][j]

        while True:
            for i in range(0,length_of):
                initial_push=chr(65+i)+"*"+str(initial_supp[chr(65+i)])
                print("-----------------------\n")
                print("Round {0}:{1}\n".format(round,chr(65+i)))
                
                clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                clientSocket.connect(socket_list[i])        # Connect with the node and retrieve dv from the node
                clientSocket.send(initial_push.encode())
                ss1=clientSocket.recv(1024).decode()
                #d,l=ss1.split("*")
                print("Current DV matrix:",ss1)
                
                print("Last DV matrix:",initial_supp[chr(65+i)])
                update_dv=ast.literal_eval(ss1)

                if update_dv==initial_supp[chr(65+i)]:
                    print("Updated from last DV matrix or the same?Same\n")
                    full_update+=1
                else:
                    print("Updated from last DV matrix or the same?Updated\n")
                    
                    initial_supp[chr(65+i)]=update_dv.copy()
                    full_update=0
                    
                
                clientSocket.shutdown(socket.SHUT_RDWR)
                clientSocket.close()
                round+=1

                for u in neighbour_dict[chr(65+i)]:   # Send the above retrieve dv to neighbour nodes
                    if u in name_list:
                        ind=name_list.index(u)
                        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        clientSocket.connect(socket_list[ind])
                        clientSocket.send((chr(65+i)+"*"+ss1).encode())
                        clientSocket.recv(1024).decode()
                        clientSocket.shutdown(socket.SHUT_RDWR)
                        clientSocket.close()
            
            if full_update>=length_of:          # Breaking condition --- break after n successive unchanged dv updations
                for i in range(0,length_of):
                    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    clientSocket.connect(socket_list[i])
                    clientSocket.send((chr(65+i)+"*"+"BYE").encode())
                    clientSocket.shutdown(socket.SHUT_RDWR)
                    clientSocket.close()
                break

        print("======================")
        print("Final output:")
        for i in initial_supp:
            print("Node {0} DV={1}".format(i,initial_supp[i]))
        print("Number of rounds till convergence (Round # when one of the nodes last updated its DV) =",round-1)
        

    else:
        print("No input files given...Try again by entering an input file")
        sys.exit(0)

    
    
    
