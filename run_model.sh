#! /bin/bash
config_file_path=$1
curr_iteration=$2
n_max_scribble_file=$3

python visium_data_to_matrix_representation_converter.py --params ${config_file_path} --curr_iteration ${curr_iteration} --n_max_scribble_files ${n_max_scribble_file}
echo "========================================"
echo "Data convertend in matrix representation"
python scribble_dom.py --params ${config_file_path} --curr_iteration ${curr_iteration} --n_max_scribble_files ${n_max_scribble_file}
echo "========================================"
echo "Model run complete"
python best_model_estimator.py --params ${config_file_path}
echo "========================================"
echo "Best model evaluated with goodness score"
python show_results.py --params ${config_file_path}