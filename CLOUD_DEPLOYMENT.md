# Cloud Deployment Guide

This guide covers options for running Claim Assist in the cloud with GPU acceleration.

## Deployment Options

### Option 1: RunPod (Recommended - Easy GPU Access)

**Best for:** GPU inference with minimal setup, pay-per-use

RunPod provides instant access to GPU servers with per-minute billing.

#### Setup Steps:

1. **Create RunPod Account**
   - Visit: https://www.runpod.io/
   - Sign up and add payment method
   - Get $10 free credit for testing

2. **Deploy a Pod**
   ```
   1. Go to "Pods" → "Deploy"
   2. Select GPU:
      - RTX 3090 (24GB): ~$0.34/hour
      - RTX 4090 (24GB): ~$0.69/hour
      - RTX A5000 (24GB): ~$0.49/hour
   3. Choose Template: "RunPod Pytorch" or "RunPod Ubuntu"
   4. Set Disk Space: 50GB minimum
   5. Click "Deploy On-Demand"
   ```

3. **Connect to Pod**
   ```bash
   # SSH into your pod (connection details shown in RunPod dashboard)
   ssh root@<pod-ip> -p <port> -i ~/.ssh/id_ed25519
   ```

4. **Install Dependencies**
   ```bash
   # Update system
   apt update && apt upgrade -y
   
   # Install required packages
   apt install -y git cmake build-essential curl
   
   # Install Python dependencies
   apt install -y python3 python3-pip
   
   # Clone your repository
   git clone https://github.com/CamdenBibro/claim-assist.git
   cd claim-assist
   
   # Install Python requirements
   pip3 install -r requirements-minimal.txt
   ```

5. **Build llama.cpp with CUDA**
   ```bash
   # Clone llama.cpp
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   
   # Build with CUDA (RunPod pods have CUDA pre-installed)
   mkdir build && cd build
   cmake .. -DLLAMA_CUDA=ON
   cmake --build . --config Release
   
   cd ../..
   ```

6. **Download Model**
   ```bash
   # Create models directory
   mkdir -p llama.cpp/models
   cd llama.cpp/models
   
   # Download Llama 3.1 8B
   curl -L -o llama-3.1-8b-instruct-q4_k_m.gguf \
     "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
   
   cd ../..
   ```

7. **Start llama.cpp Server**
   ```bash
   # Start in background
   cd llama.cpp/build/bin
   nohup ./server -m ../../models/llama-3.1-8b-instruct-q4_k_m.gguf \
     -ngl 50 \
     --port 8080 \
     --host 0.0.0.0 \
     -c 4096 > server.log 2>&1 &
   
   cd ../../..
   ```

8. **Run Claim Processing**
   ```bash
   cd claim-assist
   
   # Set environment variables
   export INFERENCE_BACKEND="llamacpp"
   export MODEL_NAME="llama-3.1-8b-instruct"
   export INFERENCE_BASE_URL="http://localhost:8080/v1"
   
   # Process claims
   python3 -m claim_assist.main example_claims.csv
   ```

9. **Download Results**
   ```bash
   # On your local machine, download the results:
   scp -P <port> -i ~/.ssh/id_ed25519 \
     root@<pod-ip>:/root/claim-assist/results_*.csv ./
   ```

10. **Stop Pod When Done**
    - RunPod charges by the minute
    - Stop the pod in the dashboard when finished
    - Your files persist if you restart the same pod

**Cost Estimate:**
- RTX 3090: ~$0.006/minute = ~$0.36/hour
- Processing 100 claims: ~10 minutes = ~$0.06
- Idle time costs money, so stop when not in use!

---

### Option 2: Google Colab (Free GPU, Limited Time)

**Best for:** Testing, small batches, free tier available

Google Colab provides free GPU access with usage limits.

#### Setup Steps:

1. **Create a Colab Notebook**
   - Visit: https://colab.research.google.com/
   - Click "New Notebook"
   - Go to Runtime → Change runtime type → GPU → T4 GPU

2. **Install Dependencies**
   ```python
   # Cell 1: Install system dependencies
   !apt-get update
   !apt-get install -y cmake build-essential
   
   # Cell 2: Clone repositories
   !git clone https://github.com/CamdenBibro/claim-assist.git
   !git clone https://github.com/ggerganov/llama.cpp
   
   # Cell 3: Build llama.cpp
   %cd llama.cpp
   !mkdir build && cd build && cmake .. -DLLAMA_CUDA=ON && cmake --build . --config Release
   %cd ..
   
   # Cell 4: Download model
   !mkdir -p models
   !curl -L -o models/llama-3.1-8b-q4.gguf \
     "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
   
   # Cell 5: Install Python dependencies
   %cd /content/claim-assist
   !pip install -r requirements-minimal.txt
   ```

3. **Start Server and Process Claims**
   ```python
   # Cell 6: Start llama.cpp server in background
   import subprocess
   import time
   
   server_process = subprocess.Popen([
       '/content/llama.cpp/build/bin/server',
       '-m', '/content/llama.cpp/models/llama-3.1-8b-q4.gguf',
       '-ngl', '50',
       '--port', '8080',
       '--host', '0.0.0.0',
       '-c', '4096'
   ])
   
   time.sleep(10)  # Wait for server to start
   print("Server started!")
   
   # Cell 7: Upload your claims CSV
   from google.colab import files
   uploaded = files.upload()  # Upload your CSV file
   
   # Cell 8: Process claims
   import os
   os.environ['INFERENCE_BACKEND'] = 'llamacpp'
   os.environ['INFERENCE_BASE_URL'] = 'http://localhost:8080/v1'
   
   !python -m claim_assist.main <your-uploaded-file>.csv
   
   # Cell 9: Download results
   files.download('results_*.csv')
   ```

**Limitations:**
- Free tier: 12 hours max session time
- Disconnects after 90 minutes of inactivity
- GPU availability not guaranteed
- Not suitable for production use

**Colab Pro Options:**
- Colab Pro: $10/month - Better GPUs (A100), longer sessions
- Colab Pro+: $50/month - Even better GPUs, priority access

---

### Option 3: Vast.ai (Cheapest GPU Option)

**Best for:** Budget-conscious users, flexible GPU selection

Vast.ai offers the cheapest GPU rentals from individuals.

#### Setup Steps:

1. **Create Vast.ai Account**
   - Visit: https://vast.ai/
   - Sign up and add credits ($5 minimum)

2. **Search for GPU**
   ```
   1. Go to "Create" → "Rent"
   2. Filter by:
      - GPU: RTX 3090, RTX 4090, or similar
      - VRAM: 16GB minimum
      - CUDA: 12.0+
   3. Sort by "Price" (lowest first)
   4. Select instance (as low as $0.20/hour for RTX 3090)
   ```

3. **Deploy Instance**
   ```
   1. Choose "pytorch/pytorch" image
   2. Set "Disk Space": 50GB
   3. Click "Rent"
   4. Connect via SSH or Jupyter
   ```

4. **Follow Same Setup as RunPod** (Steps 4-9 from Option 1)

**Cost Estimate:**
- RTX 3090: ~$0.20-$0.30/hour
- Very cheap but:
  - Reliability varies (rented from individuals)
  - May get interrupted if host needs GPU
  - Good for non-critical workloads

---

### Option 4: AWS EC2 with GPU

**Best for:** Enterprise use, production workloads, high reliability

AWS provides enterprise-grade GPU instances.

#### Setup Steps:

1. **Create AWS Account**
   - Visit: https://aws.amazon.com/
   - Sign up (requires credit card)

2. **Launch EC2 Instance**
   ```
   1. Go to EC2 Dashboard → "Launch Instance"
   2. Choose AMI: "Deep Learning AMI (Ubuntu)" - has CUDA pre-installed
   3. Choose Instance Type:
      - g4dn.xlarge (T4 16GB): ~$0.526/hour
      - g5.xlarge (A10G 24GB): ~$1.006/hour
      - p3.2xlarge (V100 16GB): ~$3.06/hour
   4. Configure Security Group:
      - Allow SSH (port 22) from your IP
      - Allow Custom TCP (port 8080) from your IP
   5. Create Key Pair and download .pem file
   6. Launch Instance
   ```

3. **Connect to Instance**
   ```bash
   # On your local machine
   chmod 400 your-key.pem
   ssh -i your-key.pem ubuntu@<instance-public-ip>
   ```

4. **Setup (CUDA pre-installed on Deep Learning AMI)**
   ```bash
   # Clone repository
   git clone https://github.com/CamdenBibro/claim-assist.git
   cd claim-assist
   pip install -r requirements-minimal.txt
   
   # Build llama.cpp
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   mkdir build && cd build
   cmake .. -DLLAMA_CUDA=ON
   cmake --build . --config Release
   cd ../..
   
   # Download model and start server (same as RunPod)
   ```

5. **Auto-shutdown to Save Costs**
   ```bash
   # Create auto-shutdown script
   cat > auto_shutdown.sh << 'EOF'
   #!/bin/bash
   # Shutdown after 2 hours of inactivity
   sudo shutdown -h +120
   EOF
   
   chmod +x auto_shutdown.sh
   ./auto_shutdown.sh
   ```

**Cost Estimate:**
- g4dn.xlarge: ~$0.526/hour
- Processing 100 claims: ~$0.10
- **Important:** Stop instance when not in use!

---

### Option 5: Azure Virtual Machines

**Best for:** Microsoft ecosystem, enterprise use

Similar to AWS but in Microsoft's cloud.

#### Key Instance Types:
- NC6s v3 (V100 16GB): ~$3.06/hour
- NC4as T4 v3 (T4 16GB): ~$0.526/hour
- ND96asr v4 (A100 40GB x8): ~$27.20/hour (overkill for this)

Setup is similar to AWS - use Azure Deep Learning VM image.

---

### Option 6: Jupyter Notebooks (Kaggle)

**Best for:** Free option, testing, learning

Kaggle provides free GPU access with limits.

1. Visit: https://www.kaggle.com/
2. Create notebook with GPU accelerator
3. Similar setup to Google Colab
4. Free tier: 30 hours/week GPU time

---

## Comparison Table

| Provider | GPU Options | Cost | Setup Difficulty | Best For |
|----------|-------------|------|------------------|----------|
| **RunPod** | RTX 3090, 4090, A5000 | $0.34-0.69/hr | ⭐⭐⭐⭐⭐ Easy | Quick GPU access |
| **Vast.ai** | Various | $0.20-0.50/hr | ⭐⭐⭐⭐ Easy | Budget users |
| **Google Colab** | T4, A100 (Pro) | Free / $10-50/mo | ⭐⭐⭐⭐⭐ Easiest | Testing, small batches |
| **AWS EC2** | T4, A10G, V100 | $0.53-3/hr | ⭐⭐⭐ Moderate | Enterprise, production |
| **Azure** | T4, V100, A100 | $0.53-27/hr | ⭐⭐⭐ Moderate | Microsoft ecosystem |
| **Kaggle** | P100, T4 | Free | ⭐⭐⭐⭐⭐ Easiest | Learning, testing |

## Cost Optimization Tips

1. **Stop Instances When Not in Use**
   - Cloud providers charge by the minute/hour
   - Always stop instances after processing
   - Set up auto-shutdown scripts

2. **Use Spot/Preemptible Instances**
   - AWS Spot Instances: ~70% cheaper
   - Can be interrupted but great for non-critical workloads

3. **Batch Processing**
   - Process multiple claim files in one session
   - Minimize setup/teardown time

4. **Choose Right GPU**
   - Small batches: T4 or RTX 3060 Ti (cheaper)
   - Large batches: RTX 3090 or A100 (faster, fewer hours)

5. **Use Reserved Instances for Regular Use**
   - AWS Reserved Instances: Up to 75% discount
   - Good if you process claims regularly

## Production Deployment

For continuous production use, consider:

### Option A: Serverless with API Gateway

Deploy as a serverless API:
1. Package application as Docker container
2. Deploy to AWS Lambda (with container support) or Google Cloud Run
3. Use API Gateway for requests
4. Scales automatically, pay per request

### Option B: Kubernetes Cluster

For high-volume processing:
1. Deploy to AWS EKS or Google GKE
2. Use autoscaling based on queue depth
3. Run llama.cpp in pods with GPU nodes
4. Enterprise-grade reliability

### Option C: Managed Service

Use inference API services:
1. Hugging Face Inference Endpoints
2. Replicate
3. RunPod Serverless
4. AWS SageMaker

## Security Considerations

When running online:

1. **API Keys & Secrets**
   - Use environment variables
   - Never commit API keys to git
   - Use cloud provider secret managers (AWS Secrets Manager, Azure Key Vault)

2. **Network Security**
   - Restrict SSH access to your IP
   - Use VPN if processing sensitive data
   - Enable HTTPS for web endpoints

3. **Data Privacy**
   - Encrypt data at rest and in transit
   - Consider data residency requirements
   - Delete temporary files after processing

4. **Access Control**
   - Use IAM roles (AWS) or Service Accounts (GCP)
   - Implement least privilege access
   - Enable audit logging

## Quick Start Script (RunPod/Vast.ai)

Save this as `cloud_setup.sh`:

```bash
#!/bin/bash

# Cloud Setup Script for Claim Assist
echo "Setting up Claim Assist on GPU instance..."

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y git cmake build-essential curl python3 python3-pip

# Clone repositories
cd ~
git clone https://github.com/CamdenBibro/claim-assist.git
git clone https://github.com/ggerganov/llama.cpp

# Build llama.cpp
cd llama.cpp
mkdir build && cd build
cmake .. -DLLAMA_CUDA=ON
cmake --build . --config Release
cd ..

# Download model
mkdir -p models
cd models
curl -L -o llama-3.1-8b-q4.gguf \
  "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
cd ..

# Install Python dependencies
cd ~/claim-assist
pip3 install -r requirements-minimal.txt

# Start server
cd ~/llama.cpp
nohup ./build/bin/server \
  -m ./models/llama-3.1-8b-q4.gguf \
  -ngl 50 \
  --port 8080 \
  --host 0.0.0.0 \
  -c 4096 > server.log 2>&1 &

echo "Setup complete!"
echo "Server starting... (check ~/llama.cpp/server.log)"
echo "To process claims: cd ~/claim-assist && python3 -m claim_assist.main your_file.csv"
```

Usage:
```bash
# Upload script to instance
scp cloud_setup.sh root@<instance-ip>:~/

# SSH into instance and run
ssh root@<instance-ip>
chmod +x cloud_setup.sh
./cloud_setup.sh
```

## Getting Help

- RunPod Discord: https://discord.gg/runpod
- Vast.ai Support: https://vast.ai/support
- AWS Documentation: https://docs.aws.amazon.com/ec2/
- For project issues: https://github.com/CamdenBibro/claim-assist/issues

## Next Steps

1. Choose a provider based on your needs and budget
2. Follow the setup instructions
3. Upload your claims CSV file
4. Process and download results
5. **Remember to stop/terminate instances when done!**
