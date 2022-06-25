// Header file to test features of sphinx-doxysummary

// Without namespace

/** @brief Foo function.*/
int foo();

/** Foo class.*/
class Foo {
  public:
    /** @brief A public attribute.*/
    int a_public_attribute;
    /** @brief A public method.
        @param x An integer.
    */
    char a_public_method(int x);

    /** @brief A friend function.
        @param left Left Foo object.
        @param right Right Foo object.
    */
    friend bool compare(const Foo & left, const Foo & right);
    /** @brief An operator.
        @param left Left Foo object.
        @param right Right Foo object.
    */
    friend Foo operator+(const Foo & left, const Foo & right);

  private:
    /** @brief A private attribute.*/
    int a_private_attribute;
    /** @brief A private method.
        @param x An integer.
    */
    char a_private_method(int x);
};

/** An enum.*/
enum class Spam {
    /** Value 1.*/
    Value_1,
    /** Value 2.*/
    Value_2,
    /** Value 3.*/
    Value_3
};

/** Value of PI.*/
#define PI 3.14

/** Set floating point precision.*/
typedef double real;

/** Union of float and int.*/
union UnionExample {
    float x;
    int i;
};

/** An arbitrary struct.*/
struct AStruct {
    /** A string.*/
    char * s;
    /** Length.*/
    unsigned int l;
};

/** A template function.

    @tparam T A typename.
    @param a First parameter.
    @param b Second parameter.
*/
template<typename T>
T template_func(T a, T b) {
    return a+b;
}

/** @brief Template class.
    @tparam T Any numeric type.
*/
template<typename T>
class TemplateClass {
  public:
    /** Default constructor with 3 numbers.
        @param a First number.
        @param b Second number.
        @param c Third number.
    */
    Abc(T a, T b, T c) : a_(a), b_(b), c_(c) {}
    /** Default destructor.*/
    ~Abc(void) {std::printf("Free Abc object.\n");}

  private:
    /** \brief First number.*/
    T a_;
    /** \brief Second number.*/
    T b_;
    /** \brief Third number.*/
    T c_;
};

namespace example {

/** @brief A scoped (namespace) varaible.*/
extern int scoped_variable;

/** @brief A scoped (namespace) function.*/
void scopred_function (int x);

/** @brief This is a function with a long name, but alias shortens the name.*/
int a_long_named_function_for_testing_alias (void);

}

/** @brief Argument is a void.*/
int func_overload (void);

/** @brief Argument is an integer.*/
int func_overload(int a);

/** @brief Arguments are two real numbers.*/
int func_overload(double x, double y);

/** @brief Argument is a constant l-value.*/
int func_overload(const double & x);

/** @brief Argument is an r-value.*/
int func_overload(double && x);

/** @brief Argument is a template std::vector.*/
int func_overload(std::vector<double> & v);