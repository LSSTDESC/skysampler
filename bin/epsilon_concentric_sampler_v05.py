from __future__ import print_function, division
import fitsio as fio
import numpy as np
import os

import skysampler.emulator as emulator

try:
    import cPickle as pickle
except:
    import pickle

tag_root = "epsilon_concentric_sample_v17"
NREPEATS = 4
NSAMPLES = 1500000
NCHUNKS = 150

LOGR_DRAW_RMINS = [-3, -0.5, 0., 0.5]
LOGR_DRAW_RMAXS = [-0.5, 0., 0.5, 1.2]
LOGR_CAT_RMAXS = [0., 0.5, 1.2, 2.]

root_path = "/e/ocean1/users/vargatn/EMULATOR/EPSILON/resamples/"
deep_data_path = "/e/ocean1/users/vargatn/EMULATOR/EPSILON/data/deep/run-ugriz-mof02_extcorr_naive-cleaned_zvals.fits"
wide_data_root = "/e/ocean1/users/vargatn/EMULATOR/EPSILON/indexer/"
wide_data_tag = "multi-indexer-epsilon_narrow-z_zoom_high-l_v004"


# bandwidths = [0.01, 0.03, 0.05, 0.07, 0.09]
bandwidths = [0.1,]
# param_tags = ["_z0_l1"]
param_tags = ["_z0_l0", "_z0_l1", "_z1_l0", "_z1_l1"]
clust_tag = "_clust"
rands_tag = "_rands"


deep_c_settings = {
    "columns": [
        ("MAG_I", "bdf_mag_dered_3"),
        ("COLOR_G_R", ("bdf_mag_dered_1", "bdf_mag_dered_2", "-")),
        ("COLOR_R_I", ("bdf_mag_dered_2", "bdf_mag_dered_3", "-")),
    ],
    "logs": [False, False, False],
    "limits": [(17, 22.5), (-1, 3), (-1, 3),],
}
deep_smc_settings = {
    "columns": [
        ("GABS", ("bdf_g_0", "bdf_g_1", "SQSUM")),
        ("SIZE", ("bdf_T", 1, "+")),
        ("FRACDEV", "bdf_fracdev"),
        ("MAG_I", "bdf_mag_dered_3"),
        ("COLOR_G_R", ("bdf_mag_dered_1", "bdf_mag_dered_2", "-")),
        ("COLOR_R_I", ("bdf_mag_dered_2", "bdf_mag_dered_3", "-")),
        ("COLOR_I_Z", ("bdf_mag_dered_3", "bdf_mag_dered_4", "-")),
        ("Z", "z_mc"),
    ],
    "logs": [False, True, False, False, False, False, False, False],
    "limits": [(0., 1.), (-1, 5), (-3, 4), (17, 25.5), (-1, 3), (-1, 3), (-1, 3), (0, 3.5)],
}
wide_cr_settings = {
    "columns": [
        ("MAG_I", "MOF_CM_MAG_CORRECTED_I"),
        ("COLOR_G_R", ("MOF_CM_MAG_CORRECTED_G", "MOF_CM_MAG_CORRECTED_R", "-")),
        ("COLOR_R_I", ("MOF_CM_MAG_CORRECTED_R", "MOF_CM_MAG_CORRECTED_I", "-")),
        ("LOGR", "DIST"),
    ],
    "logs": [False, False, False, True],
    "limits": [(17, 22.5), (-1, 3), (-1, 3), (1e-3, 50.), ],
}
wide_r_settings = {
    "columns": [
        ("MAG_I", "MOF_CM_MAG_CORRECTED_I"),
        ("LOGR", "DIST"),
    ],
    "logs": [False, True,],
    "limits": [(17, 22.5), (1e-3, 50.),],
}
columns = {
    "cols_dc": ["COLOR_G_R", "COLOR_R_I",],
    "cols_wr": ["LOGR",],
    "cols_wcr": ["COLOR_G_R", "COLOR_R_I", "LOGR",],
}

if __name__ == "__main__":

    run_tags = []
    for bin_tag in param_tags:
        for bw in bandwidths:
            tmp = (bin_tag + "_bw={:.3f}".format(bw), bin_tag, bw)
            run_tags.append(tmp)
    print(run_tags)

    root_path = root_path + tag_root + "/"
    if not os.path.isdir(root_path):
        os.mkdir(root_path)

    print("started reading")
    deep = fio.read(deep_data_path)


    for run_tag in run_tags:
        bandwidth = run_tag[2]

        fname_clust = wide_data_root + wide_data_tag + "/" + wide_data_tag + clust_tag + run_tag[1] + ".p"
        print(fname_clust)
        mdl_clust = pickle.load(open(fname_clust, "rb"))

        fname_rands = wide_data_root + wide_data_tag + "/" + wide_data_tag + rands_tag + run_tag[1] + ".p"
        print(fname_rands)
        mdl_rands = pickle.load(open(fname_rands, "rb"))

        print("finished reading...")

        nrbins = len(LOGR_DRAW_RMINS)
        print(nrbins)

        for nrep in np.arange(NREPEATS):
            tag = tag_root + run_tag[0] + "_run" + str(nrep)
            print("running repeat", nrep, "out of", NREPEATS)
            print(tag)

            master_seed = np.random.randint(0, np.iinfo(np.int32).max, 1)[0]
            rng = np.random.RandomState(seed=master_seed)
            seeds = rng.randint(0, np.iinfo(np.int32).max, nrbins * 5)

            i = 0
            print("starting concentric shell resampling")
            for i in np.arange(nrbins):
                print("rbin", i)
                outname = root_path + "/" + tag + "_{:1d}".format(master_seed) + "_rbin{:d}".format(i)
                print(outname)

                # update configs
                _deep_c_settings = emulator.construct_deep_container(deep, deep_c_settings, drop="MAG_I",
                                                                     seed=seeds[nrbins * i + 0])
                _deep_smc_settings = emulator.construct_deep_container(deep, deep_smc_settings,
                                                                       seed=seeds[nrbins * i + 1])

                tmp_wide_cr_settings = wide_cr_settings.copy()
                tmp_wide_cr_settings["limits"][-1] = (10**-3, 10**LOGR_CAT_RMAXS[i])
                _wide_cr_settings_clust = emulator.construct_wide_container(mdl_clust, tmp_wide_cr_settings,
                                                                            drop="MAG_I", seed=seeds[nrbins * i + 2])

                tmp_wide_r_settings = wide_r_settings.copy()
                tmp_wide_r_settings["limits"][-1] = (10**-3, 10**LOGR_CAT_RMAXS[i])
                _wide_r_settings_rands = emulator.construct_wide_container(mdl_rands, tmp_wide_r_settings,
                                                                           drop="MAG_I", seed=seeds[nrbins * i + 3])

                tmp_wide_cr_settings = wide_cr_settings.copy()
                tmp_wide_cr_settings["limits"][-1] = (10 ** -3, 10 ** LOGR_CAT_RMAXS[i])
                _wide_cr_settings_rands = emulator.construct_wide_container(mdl_rands, tmp_wide_cr_settings,
                                                                            drop="MAG_I", seed=seeds[nrbins * i + 4])

                # create infodicts
                infodicts, samples = emulator.make_classifier_infodicts(_wide_cr_settings_clust, _wide_r_settings_rands,
                                                                        _wide_cr_settings_rands,
                                                                        _deep_c_settings, _deep_smc_settings,
                                                                        columns, nsamples=NSAMPLES, nchunks=NCHUNKS,
                                                                        bandwidth=bandwidth,
                                                                        rmin=LOGR_DRAW_RMINS[i],
                                                                        rmax=LOGR_DRAW_RMAXS[i])

                fname = outname + "_samples.fits"
                print(fname)
                fio.write(fname, samples.to_records(), clobber=True)
                master_dict = {
                    "columns": infodicts[0]["columns"],
                    "bandwidth": infodicts[0]["bandwidth"],
                    "deep_c_settings": deep_c_settings,
                    "deep_smc_settings": deep_smc_settings,
                    "wide_r_settings": tmp_wide_r_settings,
                    "wide_cr_settings": tmp_wide_cr_settings,
                    "rmin": infodicts[0]["rmin"],
                    "rmax": infodicts[0]["rmin"],
                }
                pickle.dump(master_dict, open(outname + ".p", "wb"))
                print("calculating scores")
                result = emulator.run_scores2(infodicts)
                print("finished calculating scores")
                fname = outname + "_scores.fits"
                print(fname)
                fio.write(fname, result.to_records(), clobber=True)
