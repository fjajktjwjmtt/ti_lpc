/*
Copyright (C) 2025 BrerDawg

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

//filter_code.h
//v1.15

#ifndef filter_code_h
#define filter_code_h

#include <stdio.h>
#include <string.h>
#include <string>
#include <wchar.h>
#include <math.h>
#include <vector>
#include <complex>
#include <cmath>														//for std::cyl_bessel_i();

//#include "globals.h"					//v1.06
#include "GCProfile.h"
//#include "mgraph.h"					//v1.06
//#include "audio_formats.h"


using namespace std;



#define cn_filter_tap_limit 16384


namespace filter_code
	{
		
//	extern double kaiser_alpha;
	extern double kaiser_beta;											//v1.15
	
	enum en_filter_pass_type_tag
	{
	fpt_undefined,
	fpt_lowpass,
	fpt_highpass,
	fpt_bandpass,

	fpt_notch,

	fpt_bandpass2,                  //use by: filter_iir_2nd_order(..)
	fpt_apf,
	fpt_peakeq,
	fpt_lowshelf,
	fpt_highshelf,
	};








	//refer http://www.mikroe.com/chapters/view/72/chapter-2-fir-filters/
	enum en_filter_window_type_tag
	{
	fwt_undefined,
	fwt_rect,
	fwt_kaiser,                     // ADJUST ALSO as req: 'kaiser_beta'
	fwt_bartlett,
	fwt_hann,
	fwt_bartlett_hanning,
	fwt_hamming,
	//fwt_bohman,                   //not yet supported
	fwt_blackman,
	fwt_blackman_harris,

	fwt_lanczos1,					//v1.03
	fwt_lanczos1_5,					//v1.03
	fwt_lanczos2,					//v1.03
	fwt_lanczos3,					//v1.03
	};





	struct st_cplex_tag
	{
	double real;
	double imag;

    //conjugate
    st_cplex_tag conj() const											//v1.13
		{
		return { real, -imag };
		}

    //complex multiply
    st_cplex_tag operator*(const st_cplex_tag& rhs) const
		{
		return 
			{
			real * rhs.real - imag * rhs.imag,
			real * rhs.imag + imag * rhs.real
			};
		}
	};





	struct st_cplex_float_tag
	{
	float real;
	float imag;

    //conjugate
    st_cplex_float_tag conj() const										//v1.13
		{
		return { real, -imag };
		}

    //complex multiply
    st_cplex_float_tag operator*(const st_cplex_float_tag& rhs) const
		{
		return 
			{
			real * rhs.real - imag * rhs.imag,
			real * rhs.imag + imag * rhs.real
			};
		}
	};





	typedef struct 														//see 'create_filter_from_coeffs()' function for EXAMPLE of HOW to set this structure up
	{
	bool verb;															//verbose for debugging, v1.06
	string suser0;														//user string for debugging	v1.06
	string suser1;
	int user_id0;														//user num storage
	int user_id1;
	bool created;
	int coeff_cnt;
	double *coeff_ptr;
	double *prev;
	unsigned int prev_idx;
	bool bypass;

	} st_fir;




	//v1.03, see also, see also 'st_iir_2nd_order_tag'
	typedef struct
	{
	bool verb;															//verbose for debugging, v1.07
	string suser0;														//user string for debugging	v1.07
	string suser1;
	int user_id0;														//user num storage v1.07
	int user_id1;

	bool bypass;

	bool created;
	int coeff_cnt;
//	double *coeff_ptr;													//v1.07

	double a1, a2;
	double b0, b1, b2;

	double dly0;
	double dly1;


	} st_iir;











	//v1.02, see also 'st_iir'
	struct st_iir_2nd_order_tag
	{
	bool verb;															//verbose for debugging, v1.06
	string suser0;														//user string for debugging	v1.08
	string suser1;
	int user_id0;														//user num storage
	int user_id1;
	bool bypass;
	float coeff[5];														//a1, a2, b0, b1, b2
	float delay0[2];													//for ch0
	float delay1[2];													//for ch1
	};







	//function prototypes
	bool calc_filter_iir_2nd_order( en_filter_pass_type_tag filt_type, double fc1, double in_Q, double db_gain, double srate, vector<double> &vcoeff );
	bool filter_iir_2nd_order( vector <st_cplex_tag> &viq, double a1, double a2, double b0,  double b1, double b2, double &d0r, double &d1r, double &d0i, double &d1i );
	bool filter_fir_windowed( en_filter_window_type_tag   wnd_type, en_filter_pass_type_tag   filt_type, unsigned int taps, double fc1, double fc2, double srate, vector<double> &vcoeff );
	bool read_iowa_hills_coeffs( string fname, int section, double &a1, double &a2, double &b0, double &b1, double &b2 );


	void fir_init( st_fir &fir );
	void fir_in( st_fir &fir, double in );
	double fir_out( st_fir &fir );
	//double fir_out_inline_4( st_fir &fir );
	//double fir_out_inline_8( st_fir &fir );
	bool create_filter_from_coeffs( st_fir &fir, vector<double> &vcoeff );
	bool create_iir_filter_from_coeffs_b0_first( st_iir &iir, vector<double> &vcoeff );
	void delete_filter( st_fir &fir );

	bool create_filter_from_string( st_fir &fir, string scoeff );
	bool create_filter_from_file( st_fir &fir, string fname );

	//void filter_iir_2nd_order_slow( double &dsignal, double a1, double a2, double b0,  double b1, double b2, double &d0, double &d1 );
	void filter_iir_2nd_order( float &fsignal, st_iir_2nd_order_tag &of );	//v1.02			//NOTE this is SIMILAR to 'iir_process()'
	void filter_iir_2nd_order_2ch( float &fsig0, float &fsig1, st_iir_2nd_order_tag &of );	//v1.02

	bool create_iir_filter_from_coeffs( st_iir &iir, vector<double> &vcoeff ); //v1.03
	void iir_init( st_iir &iir ); //v1.03
	void iir_delete_filter( st_iir &iir ); //v1.03
	double iir_process( st_iir &iir, double in ); //v1.03	//NOTE this is SIMILAR to 'filter_iir_2nd_order()'
	void create_filter_iir_using_q( filter_code::en_filter_pass_type_tag filt_type, float filt_freq_in, float filt_q_in, int srate_in, filter_code::st_iir_2nd_order_tag &iir );

	int factorial( int n ); 											//v1.08
	float kaiser_Io( float x );											//v1.08

	bool window_calc_and_apply_float( en_filter_window_type_tag wnd_type, vector<float> &vsmpl, vector<float> &vwnd );	//v1.08
	bool window_function_float( en_filter_window_type_tag wnd_type, unsigned len, vector<float> &vwnd );				//v1.08

	bool load_coeffs_from_file_float( string fname, vector<float> &vcoeff );			//v1.10
	bool load_coeffs_from_file_double( string fname, vector<double> &vcoeff );			//v1.10

	void polyphase_filter_downsampler_complex( filter_code::st_cplex_float_tag *cin, unsigned int insize, vector<filter_code::st_cplex_float_tag> &vcout, vector<float> &vpolycoeff, unsigned int phase_cnt, unsigned int phase_tap_cnt );
	void polyphase_filter_downsampler_for_fft( filter_code::st_cplex_float_tag *cin, unsigned int insize, vector<filter_code::st_cplex_float_tag> &vcout, vector<float> &vpolycoeff, unsigned int phase_cnt, unsigned int phase_tap_cnt );
	void polyphase_filter_upsampler_complex( filter_code::st_cplex_float_tag *cin, unsigned int insize, vector<filter_code::st_cplex_float_tag> &vcout, vector<float> &vpolycoeff, unsigned int phase_cnt, unsigned int phase_tap_cnt, bool correct_gain );
	bool polyphase_filter_upsampler_complex_vector( vector<filter_code::st_cplex_float_tag> &vcin, vector<filter_code::st_cplex_float_tag> &vcout, vector<float> &vpolycoeff, unsigned int phase_cnt, unsigned int phase_tap_cnt, bool correct_gain );
	bool load_coeffs_from_string_float( string scoeff, vector<double> &vcoeff );
	bool load_coeffs_from_string_double( string scoeff, vector<double> &vcoeff );
	bool save_coeffs_vector_float( string fname, vector<float> &vcoeff );
	bool save_coeffs_vector_double( string fname, vector<double> &vcoeff );
	void make_string_from_coeffs_float( vector<float>vcef, string &sout );
	void make_string_from_coeffs_double( vector<double>vcef, string &sout );
	void window_kaiser_float( int ntaps, double kaiser_beta, vector<float> &vkaiser );
	void window_kaiser_double( int ntaps, double kaiser_beta, vector<double> &vkaiser );
	void make_halfband_coeffs_float( unsigned int odd_tap_cnt, vector<float> &vcef );
	void make_halfband_coeffs_double( unsigned int odd_tap_cnt, vector<double> &vcef );



	}	//namespace 'filter_code'



#endif
