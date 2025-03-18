@echo off
set config_file_expert=configs\human_dlpfc\dlpfc_config_expert.json
set curr_iteration=%1
set n_max_scribble_file=%2

python visium_data_to_matrix_representation_converter.py --params %config_file_expert% --curr_iteration %curr_iteration% --n_max_scribble_files %n_max_scribble_file%
@REM echo ========================================
@REM echo Data converted in matrix representation
python log_writer.py "Data converted in matrix representation"
python scribble_dom.py --params %config_file_expert% --curr_iteration %curr_iteration% --n_max_scribble_files %n_max_scribble_file%
@REM echo ========================================
@REM echo Model run complete
python log_writer.py "Model run complete"
python best_model_estimator.py --params %config_file_expert%
@REM echo ========================================
@REM echo Best model evaluated with goodness score
python log_writer.py "Best model evaluated with goodness score"
python show_results.py --params %config_file_expert%
