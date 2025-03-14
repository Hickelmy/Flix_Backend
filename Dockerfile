# Usa uma imagem oficial do Python
FROM python:3.10

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia os arquivos necessários para o contêiner
COPY . .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Aguarda o MySQL estar pronto antes de executar o ETL
CMD ["sh", "-c", "sleep 10 && python etl.py && python main.py"]
