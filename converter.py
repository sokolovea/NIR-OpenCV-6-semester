import os

# Import the Keras model and copy the weights
import voxelmorph as vxm
tf_model = vxm.networks.VxmDense.load('model/shapes-dice-vel-3-res-8-16-32-256f.h5', input_model=None)
weights = tf_model.get_weights()

# import VoxelMorph with pytorch backend
import importlib
import torch
os.environ['VXM_BACKEND'] = 'pytorch'
importlib.reload(vxm)

# ---- CONVERT THE KERAS/TENSORFLOW H5 MODEL TO PYTORCH ---- #

# Build a Torch model and set the weights from the Keras model
reg_args = dict(
    inshape=[160, 160, 192],
    int_steps=5,
    int_downsize=2,   # same as int_resolution=2, in keras model
    unet_half_res=True,  # same as svf_resolution=2, in keras model
    nb_unet_features=([256, 256, 256, 256], [256, 256, 256, 256, 256, 256])
)
# Create the PyTorch model
pt_model = vxm.networks.VxmDense(**reg_args)

# Load the weights onto the PyTorch model
i = 0
i_max = len(list(pt_model.named_parameters()))
torchparam = pt_model.state_dict()
for k, v in torchparam.items():
    if i < i_max:
        print("{:20s} {}".format(k, v.shape))
        if k.split('.')[-1] == 'weight':
            torchparam[k] = torch.tensor(weights[i].T)
        else:
            torchparam[k] = torch.tensor(weights[i])
        i += 1

pt_model.load_state_dict(torchparam)

# Save the PyTorch model
torch.save(pt_model, 'pt_smshapes.pt')