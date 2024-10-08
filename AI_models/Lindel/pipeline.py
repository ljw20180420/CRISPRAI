import torch
from diffusers import DiffusionPipeline, __version__
import torch.nn.functional as F
import json
import numpy as np
from pathlib import Path

class LindelPipeline(DiffusionPipeline):
    def __init__(self, indel_model, ins_model, del_model):
        super().__init__()

        self.register_modules(indel_model=indel_model, ins_model=ins_model, del_model=del_model)
        Lindel_dlen = int(round((-7 + (49 + 4 * (8 + 2 * self.del_model.linear.weight.shape[0])) ** 0.5) / 2))
        self.dstarts, self.dends = [], []
        for dlen in range(Lindel_dlen - 1, 0, -1):
            for dstart in range(-dlen - 1, 3):
                self.dstarts.append(dstart)
                self.dends.append(dstart + dlen)

    @torch.no_grad()
    def __call__(self, input_indel, input_ins, input_del):
        indel_proba = F.softmax(self.indel_model(input_indel)["logit"], dim=1)
        ins_base_proba = F.softmax(self.ins_model(input_ins)["logit"], dim=1)
        del_pos_proba = F.softmax(self.del_model(input_del)["logit"], dim=1)
        return {
            "del_proba": indel_proba[:, 0],
            "ins_proba": indel_proba[:, 1],
            "ins_base": ["A", "C", "G", "T", "AA", "AC", "AG", "AT", "CA", "CC", "CG", "CT", "GA", "GC", "GG", "GT", "TA", "TC", "TG", "TT", ">2"],
            "ins_base_proba": ins_base_proba,
            "dstart": self.dstarts,
            "dend": self.dends,
            "del_pos_proba": del_pos_proba
        }
