# Use Miniconda as the base image for Conda support
FROM continuumio/miniconda3

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy environment.yml to the container
COPY environment.yml /server/environment.yml

# Create the Conda environment
RUN conda env create -f /server/environment.yml

# Ensure the environment is activated on container start
RUN echo "source activate cxt-skunkworks-server" >> ~/.bashrc

# Copy project files to the working directory
COPY app /app

# Expose the application port
EXPOSE 8000

# Run the application with the Conda environment activated
CMD ["bash", "-c", "source activate cxt-skunkworks-server && uvicorn main:app --host 0.0.0.0 --port 8000"]
