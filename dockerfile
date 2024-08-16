FROM continuumio/anaconda3

WORKDIR /app

RUN apt-get update && apt-get install -y libgl1-mesa-glx

COPY . /app/avt_matching

RUN conda create --name avt_matching python=3.8  # Thay python=3.8 bằng phiên bản Python mà bạn cần
RUN echo "conda activate avt_matching" >> ~/.bashrc
RUN conda init bash

COPY requirements.txt .
RUN conda run -n avt_matching pip install -r requirements.txt

CMD ["bash", "-c", "source activate avt_matching && cd /app/avt_matching && python main.py --config_file /app/config.json"]