FROM continuumio/miniconda3

WORKDIR /app

COPY /home/avt/github/avt_matching /app/avt_matching

RUN conda create --name avt_matching python=3.8  # Thay python=3.8 bằng phiên bản Python mà bạn cần
RUN echo "conda activate avt_matching" >> ~/.bashrc
RUN conda init bash

COPY /home/avt/github/avt_matching/requirements.txt .
RUN conda run -n avt_matching pip install -r requirements.txt

CMD ["bash", "-c", "source activate avt_matching && cd /app/avt_matching && python main.py"]