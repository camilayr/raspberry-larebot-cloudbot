#String json_data = "{\"Sesor_id\":\"3E24R\",\"Value\":" + (String)randNumber + "}";
import serial
import time
from websocket import create_connection
import json
import boto3
import botocore
import pandas
import math



#Connect to the websocket and join the same room as the front client 
ws= create_connection("YOUR WEBSOCKET CONNECTION")
print ("Connecting to room lb")
#convierte json en una cadena 
message=json.dumps({"action":"joinroom","message":"lb"})
ws.send(message)
print ("room joined")

#Configure arduino serial to send commands
# arduino = serial.Serial(
#     port='/dev/ttyACM0', baudrate=38400, timeout=1, write_timeout=1) 


#For Windows
# arduino = serial.Serial(
#     port='COM5', baudrate=38400, timeout=1, write_timeout=1) 


anteriorPos=[90,90,90]
directions=[]
realMovement=[]
finalMovement=[]

#Diccionario para parar cuando termina el movimiento
stop = {b'END': "parar"} 


if __name__ == '__main__':
  while True:
    #Convierte el resultado como string en un diccionario
    try:
        result=json.loads(ws.recv())
        key = "message"
        print(result)
        if key in result:
            print("Key exists")
            BUCKET_NAME = 'positions-files' # replace with your bucket name
            print(result["message"])
            KEY = result["message"] # replace with your object key   
            s3 = boto3.resource('s3',
                aws_access_key_id='YOUR ACCESS KEY ID',
                aws_secret_access_key= 'YOUR SECRET ACCESS KEY')
            try:
                s3.Bucket(BUCKET_NAME).download_file(KEY, 'trayectorias.csv')
                df = pandas.read_csv('trayectorias.csv')
                print(df)
                data = df['theta0;theta1;theta2'].str.split(';', expand=True)
                #Conocer cuantas posiciones ingresaron 
                dfLength=df.shape[0]
                print("Numero de filas:",dfLength)
                print(data)
                theta0=list(data[0])
                theta1=list(data[1])
                theta2=list(data[2])
                theta0num = [int(i) for i in theta0]
                theta1num = [int(i) for i in theta1]
                theta2num = [int(i) for i in theta2]
                if all(i <= 180  for i in theta0num) and all(i <= 90 for i in theta1num) and all(i <= 90 for i in theta2num):
                    print("ejecutando")
                    # print ("Se puede ejecutar")
                    for i in range(dfLength):
                        newPos=[int(data.loc[i][0]),int(data.loc[i][1]),int(data.loc[i][2])]
                        # alert=json.dumps({"action":"message","message":"Valores inválidos"})
                        # ws.send(alert)
                        print ("posicion",newPos)
                        #Calcula la cantidad de grados que debe moverse el actuador para llegar a la posición deseada 
                        newMovement=[e1 - e2 for e1, e2 in zip(newPos,anteriorPos)]
                        #Llena el vector de posición dependiendo del signo del vector newMovement
                        for i in newMovement:
                        #Si es mayor que cero giro positivo
                            if i>0:
                                directions.append(1)
                            #Si es menor que cero giro negativo
                            else:
                                directions.append(0)
                            #Se obtiene el valor absoluto en grados que debe moverse el actuador 
                            realMovement.append(abs(i))
                        anteriorPos=newPos
                        if directions[0] == 1:
                            directions[0]=0
                        else: 
                            directions[0]=1

                        if directions[2] == 1:
                            directions[2]=0
                        else: 
                            directions[2]=1
                        for i in range(3):
                            print(i)
                            if i==0:
                                x=math.trunc(realMovement[i]*6400/360)
                                finalMovement.append(x)
                            elif i==1:
                                x=math.trunc(realMovement[i]*48960/360)
                                finalMovement.append(x)
                            elif i==2:
                                x=math.trunc(realMovement[i]*85920/360)
                                finalMovement.append(x)
                        print(finalMovement)
                        #Logs de los vectores
                        print("Movimiento:",newMovement)
                        print("Direcciones de actuador:",directions)
                        print("Valor absoluto:",realMovement)
                        commands = "{c},{d0},{d1},{d2},{q0},{q1},{q2}".format(c=1,d0=directions[0],d1=directions[1],d2=directions[2],q0=finalMovement[0],q1=finalMovement[1],q2=finalMovement[2])
                        directions=[]
                        realMovement=[]
                        finalMovement=[]
                        print(commands)

                        arduino.write(commands.encode())
                        a = 1
                        while a==1: 
                            serial_rd = arduino.readline().strip()
                            print(serial_rd) 
                            if serial_rd in stop:
                                print ("HOLA") 
                                a=0
                else:
                    print("Error en valores")
                    alert=json.dumps({"action":"message","message":"Valores inválidos"})
                    ws.send(alert)  

            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    print("The object does not exist.")
                else:
                    raise
        elif result=="Valores inválidos":
            print("Excepecion")
        else:
            print("Key does not exist") 
            newPos=[int(result["Q0"]),int(result["Q1"]),int(result["Q2"])]
            #Calcula la cantidad de grados que debe moverse el actuador para llegar a la posición deseada 
            newMovement=[e1 - e2 for e1, e2 in zip(newPos,anteriorPos)]
            #Llena el vector de posición dependiendo del signo del vector newMovement
            for i in newMovement:
            #Si es mayor que cero giro positivo
                if i>0:
                    directions.append(1)
                #Si es menor que cero giro negativo
                else:
                    directions.append(0)
                #Se obtiene el valor absoluto en grados que debe moverse el actuador 
                realMovement.append(abs(i))
            anteriorPos=newPos
            if directions[0] == 1:
                directions[0]=0
            else: 
                directions[0]=1

            if directions[2] == 1:
                directions[2]=0
            else: 
                directions[2]=1
            for i in range(3):
                print(i)
                if i==0:
                    x=math.trunc(realMovement[i]*6400/360)
                    finalMovement.append(x)
                elif i==1:
                    x=math.trunc(realMovement[i]*48960/360)
                    finalMovement.append(x)
                elif i==2:
                    x=math.trunc(realMovement[i]*85920/360)
                    finalMovement.append(x)
            print(finalMovement)
            #Logs de los vectores
            print("Movimiento:",newMovement)
            print("Direcciones de actuador:",directions)
            print("Valor absoluto:",realMovement)
            commands = "{c},{d0},{d1},{d2},{q0},{q1},{q2}".format(c=1,d0=directions[0],d1=directions[1],d2=directions[2],q0=finalMovement[0],q1=finalMovement[1],q2=finalMovement[2])
            directions=[]
            realMovement=[]
            finalMovement=[]
            print(commands)

            arduino.write(commands.encode())
            a = 1
            while a==1: 
                serial_rd = arduino.readline().strip()
                print(serial_rd) 
                if serial_rd in stop:
                    print ("HOLA") 
                    a=0
        
        print ("Recibido:",result)
    except:
        print("Error")
    # except (NameError, TypeError) as error:
    #     print(error)
    # except: 
    #     errores=json.dumps({"action":"message","message":"Ocurrió un error, vuelve a intentarlo"})
    #     ws.send(errores)
    #     # print("Error")
    
  ws.close()
    
