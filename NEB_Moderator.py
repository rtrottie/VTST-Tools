#!/usr/bin/env python
#
# submits job to queue
#
# verbose output in qperr
#
#

script="$4.sh"
let nnodes=$1
let numpernode=$2
let time=$3
let nprocs=$numpernode*$nnodes
outfile=$4

# determine which que to go into

que="normal"

if [ $3 -le 1 ]
  then que="janus-debug"
fi

if [ $3 -gt 24 ]
 then que="janus-long"
fi


echo $que



# Header for script adds nodes list from PBS
echo "#!/bin/bash" > $script
echo "#SBATCH -J $4
#SBATCH --time=$3:00:00
#SBATCH -N $1
#SBATCH --ntasks-per-node $2
#SBATCH -o $4-%j.out
#SBATCH -e $4-%j.err
#SBATCH --qos=$que " >> $script


echo "module load intel/intel-12.1.6" >> $script
echo "module load openmpi/openmpi-1.4.5_intel-12.1.6_ib" >> $script  
echo "module load fftw/fftw-3.3.3_openmpi-1.4.5_intel-12.1.0_double_ib" >> $script
 

######## run ###########
echo 'cd $PBS_O_WORKDIR' >> $script

echo "export OMP_NUM_THREADS=1" >> $script

echo "mpirun -np $nprocs /projects/musgravc/apps/red_hat6/vasp5.3.3/gamma/vasp.5.3/vasp -t /lustre/janus_scratch/$USER -d > $outfile " >> $script




echo "exit 0" >> $script

# Submit script to queue
sbatch  $script

